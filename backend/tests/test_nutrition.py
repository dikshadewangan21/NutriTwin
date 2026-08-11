from app.services.nutrition_calculator import nutrition_calculator
from app.services.safety_layer import safety_layer

def test_bmr_tdee_calculation():
    # Male 25y, 75kg, 175cm, moderate activity
    res_m = nutrition_calculator.compute_nutritional_profile(
        age=25, gender="male", height_cm=175, weight_kg=75, target_weight_kg=70,
        activity_level="moderate", fitness_goal="weight_loss"
    )
    assert res_m["bmr"] > 1600
    assert res_m["tdee"] > 2400
    assert res_m["target_calories"] < res_m["tdee"] # Deficit for weight loss
    assert res_m["target_protein_g"] >= 75*1.5

    # Female 30y, 60kg, 162cm, light activity
    res_f = nutrition_calculator.compute_nutritional_profile(
        age=30, gender="female", height_cm=162, weight_kg=60, target_weight_kg=65,
        activity_level="light", fitness_goal="muscle_gain"
    )
    assert res_f["target_calories"] > res_f["tdee"] # Surplus for muscle gain

def test_safety_allergies_filter():
    class DummyFood:
        def __init__(self, name, allergens, dietary_type):
            self.name = name
            self.allergens = allergens
            self.dietary_type = dietary_type

    foods = [
        DummyFood("Peanut Poha", ["peanuts"], "vegan"),
        DummyFood("Idli Sambar", [], "vegan"),
        DummyFood("Chicken Curry", [], "non_vegetarian")
    ]

    # Test peanut allergy exclusion
    safe = safety_layer.filter_safe_foods(foods, allergies=["peanuts"], dietary_preference="vegan")
    names = [f.name for f in safe]
    assert "Peanut Poha" not in names
    assert "Chicken Curry" not in names
    assert "Idli Sambar" in names
