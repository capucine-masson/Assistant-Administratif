import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..catalog import _points_for_difficulty
from ..database import get_db
from ..deps import resolve_user_or_redirect
from ..llm_service import extract_task_from_message
from ..models import Category, Demarche, Person

router = APIRouter()


@router.post("/chatbot/message")
async def chatbot_message(request: Request, db: Session = Depends(get_db)):
    user, redirect = resolve_user_or_redirect(request, db)
    if redirect:
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    payload = await request.json()
    message = (payload.get("message") or "").strip()
    if not message:
        return JSONResponse({"reply": "Dites-moi ce que vous devez faire, je m'occupe du reste.", "demarche": None})

    categories = db.query(Category).filter_by(user_id=user.id).order_by(Category.name).all()
    category_names = [c.name for c in categories]

    result = extract_task_from_message(message, category_names)

    category = next((c for c in categories if c.name.lower() == result["category"].lower()), None)
    if category is None:
        category = next((c for c in categories if c.name == "Autre"), categories[0] if categories else None)

    person = db.query(Person).filter_by(user_id=user.id, relation="moi").first()

    demarche = Demarche(
        user_id=user.id,
        category_id=category.id if category else None,
        person_id=person.id if person else None,
        title=result["title"],
        description=message,
        detailed_guide=result["guide"],
        status="a_faire",
        difficulty=result["difficulty"],
        estimated_minutes=result["estimated_minutes"],
        points_reward=_points_for_difficulty(result["difficulty"]),
    )
    if result.get("deadline"):
        try:
            demarche.deadline = datetime.datetime.strptime(result["deadline"], "%Y-%m-%d")
        except ValueError:
            pass
    demarche.official_urls = []
    demarche.steps = []

    db.add(demarche)
    db.commit()
    db.refresh(demarche)

    reply = f"C'est noté ! J'ai créé la démarche « {demarche.title} » dans {category.name if category else 'Autre'}."
    return JSONResponse(
        {
            "reply": reply,
            "demarche": {"id": demarche.id, "title": demarche.title, "url": f"/demarches/{demarche.id}"},
        }
    )
