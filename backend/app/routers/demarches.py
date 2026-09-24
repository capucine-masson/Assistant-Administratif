import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from .. import rewards as rewards_logic
from ..database import get_db
from ..deps import resolve_user_or_redirect
from ..llm_service import estimate_and_generate_guide
from ..models import Category, Demarche, Person
from ..templating import templates

router = APIRouter()


def _apply_filters(query, category_id, person_id, status):
    if category_id:
        query = query.filter(Demarche.category_id == category_id)
    if person_id:
        query = query.filter(Demarche.person_id == person_id)
    if status:
        query = query.filter(Demarche.status == status)
    return query


@router.get("/")
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    view: str = "list",
    category_id: str | None = None,
    person_id: str | None = None,
    status: str | None = None,
    flash: str | None = None,
    flash_type: str = "info",
):
    user, redirect = resolve_user_or_redirect(request, db)
    if redirect:
        return redirect

    category_id = int(category_id) if category_id else None
    person_id = int(person_id) if person_id else None
    status = status or None

    query = db.query(Demarche).filter(Demarche.user_id == user.id)
    query = _apply_filters(query, category_id, person_id, status)
    demarches = query.order_by(Demarche.deadline.is_(None), Demarche.deadline).all()

    categories = db.query(Category).filter_by(user_id=user.id).order_by(Category.name).all()
    people = db.query(Person).filter_by(user_id=user.id).order_by(Person.id).all()

    grouped: dict[str, list[Demarche]] = {}
    for d in demarches:
        key = d.category.name if d.category else "Sans catégorie"
        grouped.setdefault(key, []).append(d)
    grouped = dict(sorted(grouped.items()))

    counts = {
        "a_faire": sum(1 for d in demarches if d.status == "a_faire"),
        "en_cours": sum(1 for d in demarches if d.status == "en_cours"),
        "terminee": sum(1 for d in demarches if d.status == "terminee"),
        "overdue": sum(1 for d in demarches if d.is_overdue),
    }

    template = "dashboard_calendar.html" if view == "calendar" else "dashboard_list.html"
    return templates.TemplateResponse(
        request,
        template,
        {
            "user": user,
            "demarches": demarches,
            "grouped": grouped,
            "categories": categories,
            "people": people,
            "counts": counts,
            "view": view,
            "filters": {"category_id": category_id, "person_id": person_id, "status": status},
            "flash": flash,
            "flash_type": flash_type,
        },
    )


@router.get("/demarches/new")
def new_demarche_page(request: Request, db: Session = Depends(get_db)):
    user, redirect = resolve_user_or_redirect(request, db)
    if redirect:
        return redirect

    categories = db.query(Category).filter_by(user_id=user.id).order_by(Category.name).all()
    people = db.query(Person).filter_by(user_id=user.id).order_by(Person.id).all()
    return templates.TemplateResponse(
        request, "demarche_form.html", {"user": user, "categories": categories, "people": people, "demarche": None}
    )


@router.post("/demarches/new")
def create_demarche(
    request: Request,
    db: Session = Depends(get_db),
    title: str = Form(...),
    description: str = Form(""),
    category_id: int = Form(...),
    person_id: int = Form(...),
    deadline: str = Form(""),
    difficulty: str = Form(""),
    estimated_minutes: int = Form(0),
    use_ai: str = Form(""),
):
    user, redirect = resolve_user_or_redirect(request, db)
    if redirect:
        return redirect

    demarche = Demarche(
        user_id=user.id,
        category_id=category_id,
        person_id=person_id,
        title=title.strip(),
        description=description.strip(),
        status="a_faire",
    )

    if deadline:
        try:
            demarche.deadline = datetime.datetime.strptime(deadline, "%Y-%m-%d")
        except ValueError:
            demarche.deadline = None

    if use_ai == "on" or not difficulty:
        ai_result = estimate_and_generate_guide(title, description)
        demarche.difficulty = difficulty or ai_result["difficulty"]
        demarche.estimated_minutes = estimated_minutes or ai_result["estimated_minutes"]
        demarche.detailed_guide = ai_result["guide"]
    else:
        demarche.difficulty = difficulty
        demarche.estimated_minutes = estimated_minutes or 30

    demarche.points_reward = {"facile": 30, "moyen": 50, "difficile": 80}.get(demarche.difficulty, 50)
    demarche.official_urls = []
    demarche.steps = []

    db.add(demarche)
    db.commit()
    db.refresh(demarche)
    return RedirectResponse(f"/demarches/{demarche.id}", status_code=303)


@router.get("/demarches/{demarche_id}")
def demarche_detail(demarche_id: int, request: Request, db: Session = Depends(get_db)):
    user, redirect = resolve_user_or_redirect(request, db)
    if redirect:
        return redirect

    demarche = db.query(Demarche).filter_by(id=demarche_id, user_id=user.id).first()
    if demarche is None:
        return RedirectResponse("/", status_code=303)

    categories = db.query(Category).filter_by(user_id=user.id).order_by(Category.name).all()
    people = db.query(Person).filter_by(user_id=user.id).order_by(Person.id).all()

    return templates.TemplateResponse(
        request,
        "demarche_detail.html",
        {"user": user, "demarche": demarche, "categories": categories, "people": people},
    )


@router.post("/demarches/{demarche_id}/status")
def update_status(demarche_id: int, request: Request, db: Session = Depends(get_db), status: str = Form(...)):
    user, redirect = resolve_user_or_redirect(request, db)
    if redirect:
        return redirect

    demarche = db.query(Demarche).filter_by(id=demarche_id, user_id=user.id).first()
    if demarche is None:
        return RedirectResponse("/", status_code=303)

    if status == "en_cours" and demarche.started_at is None:
        demarche.started_at = datetime.datetime.utcnow()
        demarche.status = "en_cours"
        db.commit()
        return RedirectResponse(f"/demarches/{demarche_id}", status_code=303)

    if status == "terminee" and demarche.status != "terminee":
        result = rewards_logic.complete_demarche(db, demarche)
        db.commit()
        badges_str = ",".join(b.label for b in result["new_badges"])
        return RedirectResponse(
            f"/demarches/{demarche_id}?awarded={result['points_awarded']}&badges={badges_str}",
            status_code=303,
        )

    demarche.status = status
    db.commit()
    return RedirectResponse(f"/demarches/{demarche_id}", status_code=303)


@router.post("/demarches/{demarche_id}/step")
async def toggle_step(demarche_id: int, request: Request, db: Session = Depends(get_db)):
    user, redirect = resolve_user_or_redirect(request, db)
    if redirect:
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    demarche = db.query(Demarche).filter_by(id=demarche_id, user_id=user.id).first()
    if demarche is None:
        return JSONResponse({"error": "not found"}, status_code=404)

    payload = await request.json()
    index = payload.get("index")
    steps = demarche.steps
    if index is not None and 0 <= index < len(steps):
        steps[index]["done"] = not steps[index]["done"]
        demarche.steps = steps
        db.commit()

    return JSONResponse({"steps": demarche.steps})


@router.post("/demarches/{demarche_id}/edit")
def edit_demarche(
    demarche_id: int,
    request: Request,
    db: Session = Depends(get_db),
    title: str = Form(...),
    description: str = Form(""),
    category_id: int = Form(...),
    person_id: int = Form(...),
    deadline: str = Form(""),
    difficulty: str = Form("moyen"),
    estimated_minutes: int = Form(30),
    notes: str = Form(""),
):
    user, redirect = resolve_user_or_redirect(request, db)
    if redirect:
        return redirect

    demarche = db.query(Demarche).filter_by(id=demarche_id, user_id=user.id).first()
    if demarche is None:
        return RedirectResponse("/", status_code=303)

    demarche.title = title.strip()
    demarche.description = description.strip()
    demarche.category_id = category_id
    demarche.person_id = person_id
    demarche.difficulty = difficulty
    demarche.estimated_minutes = estimated_minutes
    demarche.notes = notes
    if deadline:
        try:
            demarche.deadline = datetime.datetime.strptime(deadline, "%Y-%m-%d")
        except ValueError:
            pass
    else:
        demarche.deadline = None

    db.commit()
    return RedirectResponse(f"/demarches/{demarche_id}", status_code=303)


@router.post("/demarches/{demarche_id}/delete")
def delete_demarche(demarche_id: int, request: Request, db: Session = Depends(get_db)):
    user, redirect = resolve_user_or_redirect(request, db)
    if redirect:
        return redirect

    demarche = db.query(Demarche).filter_by(id=demarche_id, user_id=user.id).first()
    if demarche:
        db.delete(demarche)
        db.commit()
    return RedirectResponse("/", status_code=303)
