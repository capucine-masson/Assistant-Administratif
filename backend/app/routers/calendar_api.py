from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Demarche

router = APIRouter()

STATUS_COLORS = {
    "a_faire": "#94a3b8",
    "en_cours": "#f59e0b",
    "terminee": "#10b981",
}


@router.get("/api/demarches/calendar")
def calendar_feed(
    request: Request,
    db: Session = Depends(get_db),
    category_id: str | None = None,
    person_id: str | None = None,
    status: str | None = None,
):
    user = get_current_user(request, db)
    if user is None:
        return JSONResponse([], status_code=401)

    category_id = int(category_id) if category_id else None
    person_id = int(person_id) if person_id else None
    status = status or None

    query = db.query(Demarche).filter(Demarche.user_id == user.id, Demarche.deadline.isnot(None))
    if category_id:
        query = query.filter(Demarche.category_id == category_id)
    if person_id:
        query = query.filter(Demarche.person_id == person_id)
    if status:
        query = query.filter(Demarche.status == status)

    events = []
    for d in query.all():
        color = "#ef4444" if d.is_overdue else STATUS_COLORS.get(d.status, "#6366f1")
        events.append(
            {
                "id": d.id,
                "title": d.title,
                "start": d.deadline.date().isoformat(),
                "url": f"/demarches/{d.id}",
                "backgroundColor": color,
                "borderColor": color,
            }
        )
    return events
