import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from .database import Base, engine
from .routers import auth, calendar_api, categories, chatbot, demarches, people, quiz, rewards
from .security import CSRF_COOKIE_NAME, CSRF_MAX_AGE_SECONDS, generate_csrf_token

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Assistant de préparation administrative")


class CSRFCookieMiddleware(BaseHTTPMiddleware):
    """Assure qu'un cookie csrf_token (lisible côté client) existe pour chaque visiteur,
    et l'expose à la requête avant le rendu du template afin que les formulaires et le
    JS puissent le renvoyer sur les requêtes qui modifient l'état (voir security.verify_csrf_*)."""

    async def dispatch(self, request, call_next):
        token = request.cookies.get(CSRF_COOKIE_NAME)
        is_new = token is None
        if is_new:
            token = generate_csrf_token()
        request.state.csrf_token = token

        response = await call_next(request)

        if is_new:
            response.set_cookie(
                CSRF_COOKIE_NAME,
                token,
                samesite="lax",
                httponly=True,
                max_age=CSRF_MAX_AGE_SECONDS,
            )
        return response


app.add_middleware(CSRFCookieMiddleware)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(quiz.router)
app.include_router(demarches.router)
app.include_router(categories.router)
app.include_router(people.router)
app.include_router(rewards.router)
app.include_router(calendar_api.router)
app.include_router(chatbot.router)
