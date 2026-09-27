from enum import Enum


class DemarcheStatus(str, Enum):
    A_FAIRE = "a_faire"
    EN_COURS = "en_cours"
    TERMINEE = "terminee"


class Difficulty(str, Enum):
    FACILE = "facile"
    MOYEN = "moyen"
    DIFFICILE = "difficile"


POINTS_BY_DIFFICULTY: dict[Difficulty, int] = {
    Difficulty.FACILE: 30,
    Difficulty.MOYEN: 50,
    Difficulty.DIFFICILE: 80,
}


def points_for_difficulty(difficulty: str) -> int:
    """Seule source de vérité pour le barème de points par difficulté."""
    try:
        return POINTS_BY_DIFFICULTY[Difficulty(difficulty)]
    except ValueError:
        return POINTS_BY_DIFFICULTY[Difficulty.MOYEN]
