from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import resolve_user_or_redirect
from ..icons import CATEGORY_ICON_LABELS
from ..models import Category
from ..templating import templates

router = APIRouter()


@router.get("/categories")
def categories_page(request: Request, db: Session = Depends(get_db)):
    user, redirect = resolve_user_or_redirect(request, db)
    if redirect:
        return redirect

    categories = db.query(Category).filter_by(user_id=user.id).order_by(Category.name).all()
    return templates.TemplateResponse(
        request,
        "categories.html",
        {"user": user, "categories": categories, "icon_choices": CATEGORY_ICON_LABELS},
    )


@router.post("/categories/new")
def create_category(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    color: str = Form("#3D348B"),
    icon: str = Form("folder"),
):
    user, redirect = resolve_user_or_redirect(request, db)
    if redirect:
        return redirect

    name = name.strip()
    if name:
        db.add(Category(user_id=user.id, name=name, color=color, icon=icon or "folder"))
        db.commit()
    return RedirectResponse("/categories", status_code=303)


@router.post("/categories/{category_id}/edit")
def edit_category(
    category_id: int,
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    color: str = Form(...),
    icon: str = Form(...),
):
    user, redirect = resolve_user_or_redirect(request, db)
    if redirect:
        return redirect

    category = db.query(Category).filter_by(id=category_id, user_id=user.id).first()
    if category:
        category.name = name.strip() or category.name
        category.color = color
        category.icon = icon or category.icon
        db.commit()
    return RedirectResponse("/categories", status_code=303)


@router.post("/categories/{category_id}/delete")
def delete_category(category_id: int, request: Request, db: Session = Depends(get_db)):
    user, redirect = resolve_user_or_redirect(request, db)
    if redirect:
        return redirect

    category = db.query(Category).filter_by(id=category_id, user_id=user.id).first()
    if category and not category.demarches:
        db.delete(category)
        db.commit()
    return RedirectResponse("/categories", status_code=303)
