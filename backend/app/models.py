import datetime
import json

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime.datetime:
    return datetime.datetime.utcnow()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    first_login_done: Mapped[bool] = mapped_column(Boolean, default=False)
    profile_json: Mapped[str] = mapped_column(Text, default="{}")
    points_total: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utcnow)

    people: Mapped[list["Person"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    categories: Mapped[list["Category"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    demarches: Mapped[list["Demarche"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    badges: Mapped[list["Badge"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    @property
    def profile(self) -> dict:
        try:
            return json.loads(self.profile_json or "{}")
        except (json.JSONDecodeError, TypeError):
            return {}

    @profile.setter
    def profile(self, value: dict) -> None:
        self.profile_json = json.dumps(value, ensure_ascii=False)

    @property
    def level(self) -> int:
        return 1 + self.points_total // 200


class Person(Base):
    __tablename__ = "people"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(120))
    relation: Mapped[str] = mapped_column(String(50), default="moi")  # moi, conjoint, enfant, parent, autre

    user: Mapped["User"] = relationship(back_populates="people")
    demarches: Mapped[list["Demarche"]] = relationship(back_populates="person")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(120))
    color: Mapped[str] = mapped_column(String(20), default="#3D348B")
    icon: Mapped[str] = mapped_column(String(40), default="folder")

    user: Mapped["User"] = relationship(back_populates="categories")
    demarches: Mapped[list["Demarche"]] = relationship(back_populates="category")


class Demarche(Base):
    __tablename__ = "demarches"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    person_id: Mapped[int | None] = mapped_column(ForeignKey("people.id"), nullable=True)

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    detailed_guide: Mapped[str] = mapped_column(Text, default="")
    official_urls_json: Mapped[str] = mapped_column(Text, default="[]")
    steps_json: Mapped[str] = mapped_column(Text, default="[]")

    status: Mapped[str] = mapped_column(String(20), default="a_faire")  # a_faire | en_cours | terminee
    difficulty: Mapped[str] = mapped_column(String(20), default="moyen")  # facile | moyen | difficile
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=30)
    notes: Mapped[str] = mapped_column(Text, default="")

    deadline: Mapped[datetime.date | None] = mapped_column(DateTime, nullable=True)
    catalog_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    points_reward: Mapped[int] = mapped_column(Integer, default=50)

    started_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    user: Mapped["User"] = relationship(back_populates="demarches")
    category: Mapped["Category"] = relationship(back_populates="demarches")
    person: Mapped["Person"] = relationship(back_populates="demarches")

    @property
    def official_urls(self) -> list:
        try:
            return json.loads(self.official_urls_json or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    @official_urls.setter
    def official_urls(self, value: list) -> None:
        self.official_urls_json = json.dumps(value, ensure_ascii=False)

    @property
    def steps(self) -> list:
        try:
            return json.loads(self.steps_json or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    @steps.setter
    def steps(self, value: list) -> None:
        self.steps_json = json.dumps(value, ensure_ascii=False)

    @property
    def is_overdue(self) -> bool:
        if not self.deadline or self.status == "terminee":
            return False
        return self.deadline.date() < datetime.date.today()


class Badge(Base):
    __tablename__ = "badges"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    code: Mapped[str] = mapped_column(String(80))
    label: Mapped[str] = mapped_column(String(200))
    icon: Mapped[str] = mapped_column(String(40), default="trophy")
    points: Mapped[int] = mapped_column(Integer, default=0)
    awarded_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped["User"] = relationship(back_populates="badges")
