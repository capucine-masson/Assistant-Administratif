from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .database import Base, engine
from .routers import auth, calendar_api, categories, chatbot, demarches, people, quiz, rewards

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Assistant de préparation administrative")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(quiz.router)
app.include_router(demarches.router)
app.include_router(categories.router)
app.include_router(people.router)
app.include_router(rewards.router)
app.include_router(calendar_api.router)
app.include_router(chatbot.router)
