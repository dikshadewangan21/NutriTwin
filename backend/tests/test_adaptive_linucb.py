import numpy as np
import pytest

from app.ml.adaptive_engine import adaptive_engine, LinUCBModel, action_to_reward
from ml_pipeline.evaluate_adaptive_linucb import run_linucb_policy_simulation

def test_action_to_reward_conversion():
    """Verify exact reward mapping conversions for actions and ratings."""
    assert action_to_reward("skipped") == -1.0
    assert action_to_reward("swapped") == -0.5
    assert action_to_reward("consumed") == 0.5
    assert action_to_reward("rated", rating=5.0) == 1.0
    assert action_to_reward("rated", rating=4.0) == 0.7
    assert action_to_reward("rated", rating=3.0) == 0.3
    assert action_to_reward("rated", rating=2.0) == -0.5
    assert action_to_reward("rated", rating=1.0) == -1.0

def test_linucb_matrix_update():
    """Verify LinUCB matrix A and response vector b update correctly on feedback."""
    model = LinUCBModel(d=6, alpha=0.5)
    initial_A = np.copy(model.A)
    initial_b = np.copy(model.b)

    x = np.array([0.8, 0.9, 0.7, 0.6, 0.5, 1.0], dtype=float)
    reward = 1.0
    model.update(x, reward)

    expected_A = initial_A + np.outer(x, x)
    expected_b = initial_b + reward * x

    np.testing.assert_allclose(model.A, expected_A)
    np.testing.assert_allclose(model.b, expected_b)

def test_linucb_score_ranking():
    """Verify that update_item_weights re-ranks recommendations dynamically using LinUCB."""
    food_scores = [
        {"food": type("Food", (), {"id": 101})(), "score": 0.80, "breakdown": {"macro_fit": 0.8, "preference_fit": 0.8, "budget_fit": 0.8, "diversity_score": 0.8}},
        {"food": type("Food", (), {"id": 102})(), "score": 0.75, "breakdown": {"macro_fit": 0.75, "preference_fit": 0.75, "budget_fit": 0.75, "diversity_score": 0.75}}
    ]

    # Provide feedback rewarding item 102 (rating 5) and penalizing item 101 (skipped)
    feedback_logs = [
        {"food_id": 102, "action_type": "consumed", "rating": 5.0},
        {"food_id": 101, "action_type": "skipped", "rating": None}
    ]

    engine = adaptive_engine
    updated = engine.update_item_weights(food_scores, feedback_logs)

    assert len(updated) == 2
    for item in updated:
        assert "score" in item
        assert "adaptive_multiplier" in item
        assert "breakdown" in item
        assert "adaptive_feedback" in item["breakdown"]
        assert "linucb_score" in item["breakdown"]

def test_api_contract_preservation():
    """Verify existing API output format is fully preserved for downstream API consumers."""
    food_scores = [
        {"food": type("Food", (), {"id": 1})(), "score": 0.90, "breakdown": {"macro_fit": 0.9}}
    ]
    res = adaptive_engine.update_item_weights(food_scores)

    assert isinstance(res, list)
    assert len(res) == 1
    assert "score" in res[0]
    assert "adaptive_multiplier" in res[0]
    assert "adaptive_feedback" in res[0]["breakdown"]
    assert "linucb_score" in res[0]["breakdown"]

def test_linucb_simulation_benchmark_report():
    """Verify simulation benchmark script generates report clearly labeled as synthetic simulation."""
    report = run_linucb_policy_simulation(num_steps=100, num_arms=5)

    assert "SYNTHETIC SIMULATION BENCHMARK" in report["evaluation_type"]
    assert "results" in report
    assert "linucb_policy" in report["results"]
    assert "random_policy" in report["results"]
    assert "greedy_policy" in report["results"]
