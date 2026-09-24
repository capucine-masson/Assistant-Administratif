"""
Authentification FACTICE : il n'y a pas de mot de passe ni de vérification
d'identité réelle. On se contente de retrouver/créer un utilisateur par son
nom d'utilisateur et de poser un cookie signé pour retenir la session.
Ne pas utiliser tel quel dans un vrai produit exposé sur internet.
"""

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from .config import settings

COOKIE_NAME = "session"
MAX_AGE_SECONDS = 60 * 60 * 24 * 30  # 30 jours

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
