import datetime

from app.catalog import compute_deadline, matches_conditions
from app.enums import points_for_difficulty


def test_points_for_known_difficulties():
    assert points_for_difficulty("facile") == 30
    assert points_for_difficulty("moyen") == 50
    assert points_for_difficulty("difficile") == 80


def test_points_for_unknown_difficulty_defaults_to_moyen():
    assert points_for_difficulty("inconnue") == 50
    assert points_for_difficulty("") == 50


def test_matches_conditions_always_true():
    assert matches_conditions({"always": True}, {}) is True


def test_matches_conditions_min_age():
    assert matches_conditions({"min_age": 18}, {"age": 17}) is False
    assert matches_conditions({"min_age": 18}, {"age": 18}) is True
    assert matches_conditions({"min_age": 18}, {}) is False


def test_matches_conditions_max_age():
    assert matches_conditions({"max_age": 25}, {"age": 26}) is False
    assert matches_conditions({"max_age": 25}, {"age": 25}) is True


def test_matches_conditions_boolean_flags():
    assert matches_conditions({"has_vehicle": True}, {"has_vehicle": True}) is True
    assert matches_conditions({"has_vehicle": True}, {"has_vehicle": False}) is False
    assert matches_conditions({"has_vehicle": True}, {}) is False


def test_matches_conditions_logement_and_profession():
    assert matches_conditions({"logement": "locataire"}, {"logement": "locataire"}) is True
    assert matches_conditions({"logement": "locataire"}, {"logement": "proprietaire"}) is False
    assert matches_conditions({"profession": "salarie"}, {"profession": "salarie"}) is True
    assert matches_conditions({"profession": "salarie"}, {"profession": "etudiant"}) is False


def test_matches_conditions_no_criteria_matches_everything():
    assert matches_conditions({}, {}) is True


def test_compute_deadline_none_type_returns_none():
    assert compute_deadline({}) is None
    assert compute_deadline({"type": "none"}) is None


def test_compute_deadline_relative_days():
    result = compute_deadline({"type": "relative_days", "days": 10})
    expected = datetime.datetime.combine(
        datetime.date.today() + datetime.timedelta(days=10), datetime.time()
    )
    assert result == expected


def test_compute_deadline_yearly_future_date_this_year():
    today = datetime.date.today()
    future = today + datetime.timedelta(days=5)
    result = compute_deadline({"type": "yearly", "month": future.month, "day": future.day})
    assert result.date() == future


def test_compute_deadline_yearly_past_date_rolls_to_next_year():
    today = datetime.date.today()
    past = today - datetime.timedelta(days=1)
    result = compute_deadline({"type": "yearly", "month": past.month, "day": past.day})
    assert result.date().year == today.year + 1
