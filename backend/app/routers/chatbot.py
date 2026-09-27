import datetime
import time

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import resolve_user_or_redirect
from ..enums import DemarcheStatus, points_for_difficulty
from ..llm_service import extract_task_from_message
from ..models import Category, Demarche, Person
from ..security import verify_csrf_header

router = APIRouter()

MIN_SECONDS_BETWEEN_MESSAGES = 2.0
DUPLICATE_WINDOW = datetime.timedelta(minutes=5)

# Anti-spam simple, en mémoire : suffisant pour une seule instance de l'app.
# Une vraie protection multi-instance nécessiterait un store partagé (Redis...).
_last_message_at: dict[int, float] = {}


@router.post("/chatbot/message", dependencies=[Depends(verify_csrf_header)])
async def chatbot_message(request: Request, db: Session = Depends(get_db)):
    user, redirect = resolve_user_or_redirect(request, db)
    if redirect:
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    now = time.monotonic()
    last = _last_message_at.get(user.id)
    if last is not None and now - last < MIN_SECONDS_BETWEEN_MESSAGES:
        return JSONResponse(
            {"error": "too_many_requests", "reply": "Merci de patienter un instant avant d'envoyer un nouveau message."},
            status_code=429,
        )
    _last_message_at[user.id] = now

    payload = await request.json()
    message = (payload.get("message") or "").strip()
    if not message:
        return JSONResponse({"reply": "Dites-moi ce que vous devez faire, je m'occupe du reste.", "demarche": None})

    duplicate = (
        db.query(Demarche)
        .filter(
            Demarche.user_id == user.id,
            Demarche.description == message,
            Demarche.created_at >= datetime.datetime.utcnow() - DUPLICATE_WINDOW,
        )
        .order_by(Demarche.created_at.desc())
        .first()
    )
    if duplicate:
        return JSONResponse(
            {
                "reply": f"Vous avez déjà une démarche similaire : « {duplicate.title} ». Je ne la duplique pas.",
                "demarche": {"id": duplicate.id, "title": duplicate.title, "url": f"/demarches/{duplicate.id}"},
            }
        )

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
        status=DemarcheStatus.A_FAIRE.value,
        difficulty=result["difficulty"],
        estimated_minutes=result["estimated_minutes"],
        points_reward=points_for_difficulty(result["difficulty"]),
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
