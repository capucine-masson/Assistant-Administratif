import datetime

from sqlalchemy.orm import Session

from .models import Badge, Demarche, User

BADGE_DEFINITIONS = {
    "premier_pas": {"label": "Premier pas", "icon": "medal", "points": 20},
    "rapide": {"label": "Rapide comme l'éclair", "icon": "zap", "points": 50},
    "zero_retard": {"label": "Zéro retard", "icon": "shield-check", "points": 50},
    "dix_demarches": {"label": "10 démarches bouclées", "icon": "trophy", "points": 100},
}


def complete_demarche(db: Session, demarche: Demarche) -> dict:
    """Marque une démarche comme terminée, calcule les points et attribue
    les éventuels badges. Retourne un résumé pour affichage à l'utilisateur."""
    now = datetime.datetime.utcnow()
    demarche.status = "terminee"
    demarche.completed_at = now
    if demarche.started_at is None:
        demarche.started_at = now

    points = demarche.points_reward
    bonus_reason = None

    if demarche.deadline:
        days_early = (demarche.deadline - now).days
        if days_early > 0:
            bonus = min(days_early * 2, 40)
            points += bonus
            bonus_reason = f"+{bonus} points pour l'avoir faite {days_early} jour(s) avant la deadline"

    user: User = demarche.user
    user.points_total += points

    new_badges = _check_badges(db, user)

    db.flush()
    return {"points_awarded": points, "bonus_reason": bonus_reason, "new_badges": new_badges}


def _check_badges(db: Session, user: User) -> list[Badge]:
    existing_codes = {b.code for b in user.badges}
    completed = [d for d in user.demarches if d.status == "terminee"]
    new_badges: list[Badge] = []

    def award(code: str):
        if code in existing_codes:
            return
        meta = BADGE_DEFINITIONS[code]
        badge = Badge(user_id=user.id, code=code, label=meta["label"], icon=meta["icon"], points=meta["points"])
        db.add(badge)
        user.points_total += meta["points"]
        new_badges.append(badge)
        existing_codes.add(code)

    if len(completed) >= 1:
        award("premier_pas")

    if len(completed) >= 10:
        award("dix_demarches")

    early_completions = [
        d for d in completed if d.deadline and d.completed_at and d.completed_at < d.deadline
    ]
    if len(early_completions) >= 5:
        award("rapide")

    overdue = [d for d in user.demarches if d.is_overdue]
    if len(overdue) == 0 and len(completed) >= 3:
        award("zero_retard")

    return new_badges
