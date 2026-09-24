import datetime
import json

from sqlalchemy.orm import Session

from .config import settings
from .models import Category, Demarche, Person

DEFAULT_CATEGORIES = {
    "Impôts": {"color": "#F7B801", "icon": "banknote"},
    "Identité": {"color": "#3D348B", "icon": "id-card"},
    "Permis & Véhicule": {"color": "#F18701", "icon": "car"},
    "Logement & CAF": {"color": "#7678ED", "icon": "house"},
    "Famille & CAF": {"color": "#F18701", "icon": "users"},
    "Scolarité": {"color": "#3D348B", "icon": "graduation-cap"},
    "Santé": {"color": "#7678ED", "icon": "heart-pulse"},
    "Emploi": {"color": "#F7B801", "icon": "briefcase"},
    "Étranger & Nationalité": {"color": "#3D348B", "icon": "globe"},
    "Retraite": {"color": "#7678ED", "icon": "landmark"},
    "Citoyenneté": {"color": "#F18701", "icon": "vote"},
    "Autre": {"color": "#64748b", "icon": "folder"},
}


def load_catalog() -> dict:
    if not settings.CATALOG_PATH.exists():
        return {"last_updated": None, "demarches": []}
    with open(settings.CATALOG_PATH, encoding="utf-8") as f:
        return json.load(f)


def ensure_default_categories(db: Session, user_id: int) -> dict[str, Category]:
    existing = {c.name: c for c in db.query(Category).filter_by(user_id=user_id).all()}
    for name, meta in DEFAULT_CATEGORIES.items():
        if name not in existing:
            cat = Category(user_id=user_id, name=name, color=meta["color"], icon=meta["icon"])
            db.add(cat)
            existing[name] = cat
    db.flush()
    return existing


def _age(profile: dict) -> int | None:
    return profile.get("age")


def matches_conditions(conditions: dict, profile: dict) -> bool:
    if conditions.get("always"):
        return True

    age = _age(profile)
    if "min_age" in conditions and (age is None or age < conditions["min_age"]):
        return False
    if "max_age" in conditions and (age is None or age > conditions["max_age"]):
        return False

    for key in ("has_permis", "has_vehicle", "has_children", "nationalite_etrangere"):
        if key in conditions and bool(profile.get(key, False)) != bool(conditions[key]):
            return False

    if "logement" in conditions and profile.get("logement") != conditions["logement"]:
        return False

    if "profession" in conditions and profile.get("profession") != conditions["profession"]:
        return False

    return True


def compute_deadline(rule: dict) -> datetime.datetime | None:
    if not rule or rule.get("type") in (None, "none"):
        return None

    today = datetime.date.today()
    if rule["type"] == "yearly":
        year = today.year
        candidate = datetime.date(year, rule["month"], rule["day"])
        if candidate < today:
            candidate = datetime.date(year + 1, rule["month"], rule["day"])
        return datetime.datetime.combine(candidate, datetime.time())

    if rule["type"] == "relative_days":
        return datetime.datetime.combine(today + datetime.timedelta(days=rule["days"]), datetime.time())

    return None


def generate_demarches_for_profile(db: Session, user_id: int, person_id: int, profile: dict) -> list[Demarche]:
    """À partir des réponses du quiz, crée les démarches pertinentes issues du catalogue."""
    categories = ensure_default_categories(db, user_id)
    catalog = load_catalog()

    created: list[Demarche] = []
    for entry in catalog.get("demarches", []):
        if not matches_conditions(entry.get("conditions", {}), profile):
            continue

        category = categories.get(entry["category"], categories["Autre"])
        demarche = Demarche(
            user_id=user_id,
            category_id=category.id,
            person_id=person_id,
            title=entry["title"],
            description=entry.get("description", ""),
            detailed_guide=entry.get("detailed_guide", ""),
            status="a_faire",
            difficulty=entry.get("difficulty", "moyen"),
            estimated_minutes=entry.get("estimated_minutes", 30),
            deadline=compute_deadline(entry.get("deadline_rule", {})),
            catalog_id=entry["id"],
            points_reward=_points_for_difficulty(entry.get("difficulty", "moyen")),
        )
        demarche.official_urls = entry.get("official_urls", [])
        demarche.steps = [{"label": s, "done": False} for s in entry.get("steps", [])]
        db.add(demarche)
        created.append(demarche)

    db.flush()
    return created


def _points_for_difficulty(difficulty: str) -> int:
    return {"facile": 30, "moyen": 50, "difficile": 80}.get(difficulty, 50)
