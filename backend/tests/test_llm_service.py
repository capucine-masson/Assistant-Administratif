import pytest

from app import llm_service
from app.config import settings


@pytest.fixture(autouse=True)
def force_no_llm_provider(monkeypatch):
    """Ces tests couvrent la logique pure (heuristique/parsing), jamais l'appel réseau réel."""
    monkeypatch.setattr(settings, "LLM_PROVIDER", "none")


def test_heuristic_estimate_detects_hard_keywords():
    result = llm_service._heuristic_estimate("Titre de séjour", "")
    assert result["difficulty"] == "difficile"
    assert result["estimated_minutes"] == 120


def test_heuristic_estimate_detects_easy_keywords():
    result = llm_service._heuristic_estimate("Vérifier mon dossier", "")
    assert result["difficulty"] == "facile"
    assert result["estimated_minutes"] == 20


def test_heuristic_estimate_defaults_to_moyen():
    result = llm_service._heuristic_estimate("Faire un truc quelconque", "")
    assert result["difficulty"] == "moyen"
    assert result["estimated_minutes"] == 45


def test_heuristic_estimate_is_case_insensitive():
    result = llm_service._heuristic_estimate("PRÉFECTURE", "")
    assert result["difficulty"] == "difficile"


def test_extract_json_parses_embedded_object():
    text = 'Voici la réponse : {"difficulty": "facile", "estimated_minutes": 10} merci'
    assert llm_service._extract_json(text) == {"difficulty": "facile", "estimated_minutes": 10}


def test_extract_json_returns_none_when_no_braces():
    assert llm_service._extract_json("pas de json ici") is None


def test_extract_json_returns_none_on_invalid_json():
    assert llm_service._extract_json("{invalid json}") is None


def test_estimate_and_generate_guide_falls_back_to_heuristic_without_provider():
    result = llm_service.estimate_and_generate_guide("Renouveler passeport", "")
    assert result["difficulty"] in {"facile", "moyen", "difficile"}
    assert isinstance(result["estimated_minutes"], int)
    assert "Étapes suggérées" in result["guide"]


def test_extract_task_from_message_falls_back_without_provider():
    result = llm_service.extract_task_from_message("Renouveler mon passeport avant le voyage", ["Papiers", "Autre"])
    assert result["title"] == "Renouveler mon passeport avant le voyage"
    assert result["category"] == "Autre"
    assert result["deadline"] is None
    assert result["difficulty"] in {"facile", "moyen", "difficile"}


def test_extract_task_from_message_truncates_long_title_to_80_chars():
    long_message = "x" * 200
    result = llm_service.extract_task_from_message(long_message, [])
    assert result["title"] == "x" * 80


def test_extract_task_from_message_defaults_when_message_is_blank():
    result = llm_service.extract_task_from_message("   ", [])
    assert result["title"] == "Nouvelle démarche"
