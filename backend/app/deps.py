from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .security import COOKIE_NAME, read_session_cookie


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    user_id = read_session_cookie(request.cookies.get(COOKIE_NAME))
    if user_id is None:
        return None
    return db.get(User, user_id)


def resolve_user_or_redirect(
    request: Request, db: Session, require_onboarded: bool = True
) -> tuple[User | None, RedirectResponse | None]:
    """Petit helper utilisé au début de chaque route protégée :

        user, redirect = resolve_user_or_redirect(request, db)
        if redirect:
            return redirect
    """
    user = get_current_user(request, db)
    if user is None:
        return None, RedirectResponse("/login", status_code=303)
    if require_onboarded and not user.first_login_done:
        return None, RedirectResponse("/quiz", status_code=303)
    return user, None
