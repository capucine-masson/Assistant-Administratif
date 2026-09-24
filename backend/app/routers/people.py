from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import resolve_user_or_redirect
from ..models import Person
from ..templating import templates

router = APIRouter()


@router.get("/people")
def people_page(request: Request, db: Session = Depends(get_db)):
    user, redirect = resolve_user_or_redirect(request, db)
    if redirect:
        return redirect

    people = db.query(Person).filter_by(user_id=user.id).order_by(Person.id).all()
    return templates.TemplateResponse(request, "people.html", {"user": user, "people": people})


@router.post("/people/new")
def create_person(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    relation: str = Form("autre"),
):
    user, redirect = resolve_user_or_redirect(request, db)
    if redirect:
        return redirect

    name = name.strip()
    if name:
        db.add(Person(user_id=user.id, name=name, relation=relation))
        db.commit()
    return RedirectResponse("/people", status_code=303)


@router.post("/people/{person_id}/delete")
def delete_person(person_id: int, request: Request, db: Session = Depends(get_db)):
    user, redirect = resolve_user_or_redirect(request, db)
    if redirect:
        return redirect

    person = db.query(Person).filter_by(id=person_id, user_id=user.id).first()
    if person and person.relation != "moi" and not person.demarches:
        db.delete(person)
        db.commit()
    return RedirectResponse("/people", status_code=303)
