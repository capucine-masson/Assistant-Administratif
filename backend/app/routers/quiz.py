from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..catalog import generate_demarches_for_profile
from ..database import get_db
from ..deps import get_current_user
from ..models import Person
from ..templating import templates

router = APIRouter()


@router.get("/quiz")
def quiz_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    if user.first_login_done:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request, "quiz.html", {"user": user})


@router.post("/quiz")
def quiz_submit(
    request: Request,
    db: Session = Depends(get_db),
    age: int = Form(...),
    sexe: str = Form(...),
    pays_residence: str = Form("France"),
    nationalite_etrangere: str = Form("non"),
    situation_familiale: str = Form("celibataire"),
    has_children: str = Form("non"),
    nb_enfants: int = Form(0),
    profession: str = Form("salarie"),
    logement: str = Form("locataire"),
    has_permis: str = Form("non"),
    has_vehicle: str = Form("non"),
):
    user = get_current_user(request, db)
    if user is None:
        return RedirectResponse("/login", status_code=303)

    profile = {
        "age": age,
        "sexe": sexe,
        "pays_residence": pays_residence.strip() or "France",
        "nationalite_etrangere": nationalite_etrangere == "oui",
        "situation_familiale": situation_familiale,
        "has_children": has_children == "oui",
        "nb_enfants": nb_enfants if has_children == "oui" else 0,
        "profession": profession,
        "logement": logement,
        "has_permis": has_permis == "oui",
        "has_vehicle": has_vehicle == "oui",
    }
    user.profile = profile
    user.first_login_done = True

    moi = db.query(Person).filter_by(user_id=user.id, relation="moi").first()
    if moi is None:
        moi = Person(user_id=user.id, name="Moi", relation="moi")
        db.add(moi)
        db.flush()

    generate_demarches_for_profile(db, user.id, moi.id, profile)

    db.commit()
    return RedirectResponse("/?flash=Bienvenue+!+Vos+démarches+ont+été+générées&flash_type=success", status_code=303)
