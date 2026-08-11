HEALTH_CONDITION_MASTER_DATA = [
    {"code": "none", "name": "None", "category": "general", "requires_dynamic_survey": False},
    {"code": "diabetes", "name": "Diabetes (Type 1 / Type 2)", "category": "metabolic", "requires_dynamic_survey": True},
    {"code": "prediabetes", "name": "Prediabetes", "category": "metabolic", "requires_dynamic_survey": True},
    {"code": "hypertension", "name": "Hypertension (High Blood Pressure)", "category": "cardiovascular", "requires_dynamic_survey": True},
    {"code": "high_cholesterol", "name": "High Cholesterol / Hyperlipidemia", "category": "cardiovascular", "requires_dynamic_survey": True},
    {"code": "pcos", "name": "PCOS / PCOD", "category": "hormonal", "requires_dynamic_survey": True},
    {"code": "thyroid", "name": "Thyroid Condition (Hypo/Hyper)", "category": "hormonal", "requires_dynamic_survey": False},
    {"code": "anemia", "name": "Anemia (Iron Deficiency)", "category": "hematologic", "requires_dynamic_survey": True},
    {"code": "heart_condition", "name": "Heart-Related Condition", "category": "cardiovascular", "requires_dynamic_survey": False},
    {"code": "kidney_condition", "name": "Kidney-Related Condition", "category": "renal", "requires_dynamic_survey": False},
    {"code": "liver_condition", "name": "Liver-Related Condition", "category": "hepatic", "requires_dynamic_survey": False},
    {"code": "gi_condition", "name": "Digestive / GI Condition (IBS, Acid Reflux)", "category": "gastrointestinal", "requires_dynamic_survey": False},
    {"code": "other", "name": "Other Condition", "category": "general", "requires_dynamic_survey": False}
]

CONDITION_SPECIFIC_SURVEYS = {
    "diabetes": [
        {"id": "diabetes_type", "question": "Diabetes classification (if diagnosed)", "options": ["Type 2", "Type 1", "Gestational", "Uncertain"]},
        {"id": "typical_carb_intake", "question": "Typical meal pattern for carbohydrates", "options": ["High rice/roti intake", "Balanced carbs", "Low carb diet"]},
        {"id": "monitors_glucose", "question": "Do you routinely monitor blood glucose?", "options": ["Yes, daily", "Occasionally", "No"]},
        {"id": "clinician_diet_restriction", "question": "Have you been given specific dietary restrictions by a doctor?", "options": ["Yes", "No"]}
    ],
    "hypertension": [
        {"id": "salt_preference", "question": "Typical salt & condiment intake preference", "options": ["High salt / papad / pickles", "Moderate salt", "Low salt"]},
        {"id": "processed_food_freq", "question": "Frequency of eating processed or packaged foods", "options": ["Frequently (3+ times/wk)", "Occasionally", "Rarely"]}
    ],
    "pcos": [
        {"id": "pcos_primary_goal", "question": "Primary focus for PCOS management", "options": ["Weight management & insulin sensitivity", "Hormonal balance", "Energy improvement"]}
    ],
    "anemia": [
        {"id": "iron_food_freq", "question": "Frequency of eating iron-rich foods (spinach, legumes, sprouts)", "options": ["Daily", "2-3 times a week", "Rarely"]}
    ]
}

class HealthConditionRulesEngine:
    """
    Configurable knowledge base defining nutritional constraints,
    portion guidelines, and food compatibility rules per health condition.
    """
    def aggregate_condition_constraints(self, selected_conditions, condition_details={}):
        """Aggregates constraints from multiple selected health conditions."""
        conditions = [c.lower() for c in (selected_conditions or []) if c.lower() != "none"]
        
        aggregated = {
            "max_glycemic_index": "High", # 'Low', 'Medium', 'High'
            "max_sodium_level": "Normal", # 'Low', 'Normal'
            "max_saturated_fat_g": 25.0,
            "min_daily_fiber_g": 25.0,
            "excluded_food_tags": [],
            "preferred_food_tags": [],
            "max_carbs_per_meal_g": 90.0,
            "iron_pairing_required": False
        }

        if not conditions:
            return aggregated

        # Diabetes / Prediabetes
        if "diabetes" in conditions or "prediabetes" in conditions:
            aggregated["max_glycemic_index"] = "Medium"
            aggregated["min_daily_fiber_g"] = max(aggregated["min_daily_fiber_g"], 30.0)
            aggregated["max_carbs_per_meal_g"] = min(aggregated["max_carbs_per_meal_g"], 55.0)
            aggregated["preferred_food_tags"].extend(["high_fiber", "low_gi", "complex_carbs"])
            aggregated["excluded_food_tags"].extend(["high_sugar", "refined_flour"])

        # Hypertension
        if "hypertension" in conditions or "heart_condition" in conditions:
            aggregated["max_sodium_level"] = "Low"
            aggregated["preferred_food_tags"].extend(["potassium_rich", "heart_healthy", "low_sodium"])

        # High Cholesterol
        if "high_cholesterol" in conditions:
            aggregated["max_saturated_fat_g"] = 14.0
            aggregated["min_daily_fiber_g"] = max(aggregated["min_daily_fiber_g"], 28.0)
            aggregated["preferred_food_tags"].extend(["soluble_fiber", "plant_sterols"])
            aggregated["excluded_food_tags"].extend(["high_trans_fat", "deep_fried"])

        # PCOS
        if "pcos" in conditions:
            aggregated["max_glycemic_index"] = "Medium"
            aggregated["min_daily_fiber_g"] = max(aggregated["min_daily_fiber_g"], 28.0)
            aggregated["preferred_food_tags"].extend(["anti_inflammatory", "lean_protein"])

        # Anemia
        if "anemia" in conditions:
            aggregated["iron_pairing_required"] = True
            aggregated["preferred_food_tags"].extend(["iron_rich", "vitamin_c_pairing"])

        return aggregated

health_condition_rules = HealthConditionRulesEngine()
