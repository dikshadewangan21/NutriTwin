import pytest
from app.ml.progress_predictor import progress_predictor, ProgressPredictorModel

def test_progress_predictor_insufficient_data_object_profile():
    """Verify that progress_predictor handles user profiles gracefully with insufficient data status."""
    class MockUserProfile:
        current_weight_kg = 75.5
        target_weight_kg = 70.0
        target_calories = 2000.0
        tdee = 2300.0

    profile = MockUserProfile()
    result = progress_predictor.predict_4week_progress(profile)

    assert result["status"] == "insufficient_data"
    assert "insufficient longitudinal" in result["message"].lower()
    assert result["current_weight_kg"] == 75.5
    assert result["target_weight_kg"] == 70.0
    assert result["weekly_forecast"] == []
    assert result["goal_achievement_probability_pct"] is None
    assert result["forecast_model"] == "None (Insufficient Data)"
    assert "minimum of 4-12 weeks" in result["uncertainty_note"].lower()

def test_progress_predictor_insufficient_data_dict_profile():
    """Verify dict input format backward compatibility."""
    profile_dict = {
        "current_weight_kg": 62.0,
        "target_weight_kg": 60.0
    }
    result = progress_predictor.predict_4week_progress(profile_dict)

    assert result["status"] == "insufficient_data"
    assert result["current_weight_kg"] == 62.0
    assert result["target_weight_kg"] == 60.0
    assert result["weekly_forecast"] == []
    assert result["goal_achievement_probability_pct"] is None

def test_no_synthetic_training_baseline():
    """Confirm that ProgressPredictor does not contain synthetic training methods or random baseline fits."""
    predictor = ProgressPredictorModel()
    assert not hasattr(predictor, "_fit_baseline")
    assert not hasattr(predictor, "rf_model")
    assert predictor.is_evaluated is False
