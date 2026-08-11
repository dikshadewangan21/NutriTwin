from app.services.health_condition_classifier import health_condition_classifier
from app.services.health_condition_rules import health_condition_rules
from app.services.nutrition_calculator import nutrition_calculator

def test_health_pathway_classification():
    # Test Diabetes + Gym pathway
    res_db = health_condition_classifier.classify_user_pathway(
        selected_conditions=["diabetes"],
        workout_type="Gym / Strength Training",
        fitness_goal="weight_loss"
    )
    assert "Diabetes-Aware" in res_db["classified_pathway"]
    assert "Strength Training" in res_db["classified_pathway"]
    assert res_db["aggregated_constraints"]["max_glycemic_index"] == "Medium"

    # Test Multi-Condition (Diabetes + High Cholesterol + Hypertension)
    res_multi = health_condition_classifier.classify_user_pathway(
        selected_conditions=["diabetes", "high_cholesterol", "hypertension"],
        workout_type="Yoga",
        fitness_goal="health"
    )
    assert res_multi["is_multi_condition"] is True
    assert "Lipid-Aware" in res_multi["classified_pathway"]
    assert res_multi["aggregated_constraints"]["max_sodium_level"] == "Low"
    assert res_multi["aggregated_constraints"]["max_saturated_fat_g"] <= 15.0

def test_high_risk_clinical_referral():
    res_kidney = health_condition_classifier.classify_user_pathway(
        selected_conditions=["kidney_condition"],
        workout_type="Walking"
    )
    assert res_kidney["clinical_referral_needed"] is True
    assert res_kidney["clinical_notice"] is not None

def test_recalculation_math():
    nutr_1 = nutrition_calculator.compute_nutritional_profile(
        age=30, gender="male", height_cm=175, weight_kg=80, target_weight_kg=75,
        activity_level="moderate", fitness_goal="weight_loss"
    )
    # Weight drops to 76kg
    nutr_2 = nutrition_calculator.compute_nutritional_profile(
        age=30, gender="male", height_cm=175, weight_kg=76, target_weight_kg=75,
        activity_level="moderate", fitness_goal="weight_loss"
    )
    assert nutr_2["bmr"] < nutr_1["bmr"]
    assert nutr_2["tdee"] < nutr_1["tdee"]
