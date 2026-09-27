"""
Authentification FACTICE : il n'y a pas de mot de passe ni de vérification
d'identité réelle. On se contente de retrouver/créer un utilisateur par son
nom d'utilisateur et de poser un cookie signé pour retenir la session.
Ne pas utiliser tel quel dans un vrai produit exposé sur internet.
"""

import secrets

from fastapi import Form, HTTPException, Request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from .config import settings

COOKIE_NAME = "session"
MAX_AGE_SECONDS = 60 * 60 * 24 * 30  # 30 jours

CSRF_COOKIE_NAME = "csrf_token"
CSRF_MAX_AGE_SECONDS = 60 * 60 * 24 * 30  # 30 jours

_serializer = URLSafeTimedSerializer(settings.SECRET_KEY, salt="assistant-admin-session")


def create_session_cookie(user_id: int) -> str:
    return _serializer.dumps({"user_id": user_id})


def read_session_cookie(cookie_value: str | None) -> int | None:
    if not cookie_value:
        return None
    try:
        data = _serializer.loads(cookie_value, max_age=MAX_AGE_SECONDS)
        return data.get("user_id")
    except (BadSignature, SignatureExpired):
        return None


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def _csrf_cookie_value(request: Request) -> str | None:
    return request.cookies.get(CSRF_COOKIE_NAME)


def verify_csrf_form(request: Request, csrf_token: str = Form(...)) -> None:
    """Dépendance à ajouter sur les routes POST alimentées par un <form>."""
    cookie_token = _csrf_cookie_value(request)
    if not cookie_token or not secrets.compare_digest(cookie_token, csrf_token):
        raise HTTPException(status_code=403, detail="CSRF token invalide ou manquant.")


def verify_csrf_header(request: Request) -> None:
    """Dépendance à ajouter sur les routes POST appelées en JSON via fetch()."""
    cookie_token = _csrf_cookie_value(request)
    header_token = request.headers.get("X-CSRF-Token")
    if not cookie_token or not header_token or not secrets.compare_digest(cookie_token, header_token):
        raise HTTPException(status_code=403, detail="CSRF token invalide ou manquant.")
