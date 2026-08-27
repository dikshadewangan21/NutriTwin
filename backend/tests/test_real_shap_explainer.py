import sys
from pathlib import Path
import pytest

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.ml.explainable_ai import explainable_ai
from app.ml.hybrid_recommender import hybrid_recommender

class MockUserProfile:
    full_name = "Jane Doe"
    dietary_preference = "vegetarian"
    daily_budget_inr = 300.0
    liked_foods = ["paneer", "sprouts"]
    disliked_foods = ["bitter gourd"]
    location_region = "North India"
    allergies = []

class MockFoodItem:
    def __init__(self, item_id, name, cal, pro, carbs, fat, fiber, cost, cat="lunch", region="North India"):
        self.id = item_id
        self.name = name
        self.calories = cal
        self.protein_g = pro
        self.carbs_g = carbs
        self.fat_g = fat
        self.fiber_g = fiber
        self.approx_cost_inr = cost
        self.category = cat
        self.dietary_type = "vegetarian"
        self.glycemic_index = "Low"
        self.allergens = []
        self.region = region

def test_real_shap_explainer_integration():
    user = MockUserProfile()
    food = MockFoodItem(101, "Paneer Tikka", 260, 20, 8, 14, 3.5, 75)

    target_macros = {"calories": 500, "protein_g": 25, "carbs_g": 50, "fat_g": 15}
    health_constraints = {"max_glycemic_index": "Medium", "max_saturated_fat_g": 20.0, "min_daily_fiber_g": 25.0}

    # 1. Score food
    scored = hybrid_recommender.score_and_rank_foods(
        food_items=[food],
        user_profile=user,
        target_macros=target_macros,
        meal_type="lunch",
        health_constraints=health_constraints
    )

    assert len(scored) == 1
    score_item = scored[0]

    # 2. Generate SHAP explanation
    explanation = explainable_ai.explain_recommendation(
        food_item=food,
        score_item=score_item,
        user_profile=user,
        remaining_macros={"protein_g": 20.0},
        health_pathway="Metabolic Health Pathway"
    )

    # 3. Assertions
    assert explanation["food_id"] == 101
    assert explanation["food_name"] == "Paneer Tikka"
    assert explanation["explainability_model"] == "SHAP TreeExplainer (XAI)"
    
    contributions = explanation["shap_feature_contributions"]
    assert len(contributions) == 6

    # Verify every feature has contribution_pct, shap_value, and impact
    total_pct = 0.0
    for feat in contributions:
        assert "feature" in feat
        assert "contribution_pct" in feat
        assert "impact" in feat
        assert feat["impact"] in ["positive", "negative"]
        assert feat["contribution_pct"] >= 0.0
        total_pct += feat["contribution_pct"]

    # Verify percentages sum approximately to 100%
    assert abs(total_pct - 100.0) < 1.0

    print("\nSHAP Explanation Result Sample:")
    print(explanation)

if __name__ == "__main__":
    test_real_shap_explainer_integration()
