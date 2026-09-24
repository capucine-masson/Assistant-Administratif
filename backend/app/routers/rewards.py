from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import resolve_user_or_redirect
from ..models import Badge
from ..templating import templates

router = APIRouter()


@router.get("/rewards")
def rewards_page(request: Request, db: Session = Depends(get_db)):
    user, redirect = resolve_user_or_redirect(request, db)
    if redirect:
        return redirect

    badges = db.query(Badge).filter_by(user_id=user.id).order_by(Badge.awarded_at.desc()).all()
    completed_count = sum(1 for d in user.demarches if d.status == "terminee")
    points_to_next_level = 200 - (user.points_total % 200)

    return templates.TemplateResponse(
        request,
        "rewards.html",
        {
            "user": user,
            "badges": badges,
            "completed_count": completed_count,
            "points_to_next_level": points_to_next_level,
        },
    )
