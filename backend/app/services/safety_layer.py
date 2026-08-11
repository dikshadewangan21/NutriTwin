class SafetyGuardrails:
    """
    Safety, Allergen, and Clinical Disclaimer Guardrails Engine.
    Excludes hazardous items, flags extreme calories, and warns for medical conditions.
    """
    MEDICAL_WARNING_CONDITIONS = ["diabetes", "renal_disease", "pregnancy", "eating_disorder", "hypertension"]

    def validate_user_safety(self, user_profile):
        """Inspects user profile for safety warnings or clinical referrals."""
        warnings = []
        requires_clinical_referral = False
        disclaimer = "NutriTwin recommendations are for general wellness and lifestyle optimization. They do not constitute medical diagnosis or clinical treatment."

        # Medical conditions check
        user_meds = [m.lower() for m in (user_profile.medical_conditions or [])]
        matched_meds = [m for m in user_meds if m in self.MEDICAL_WARNING_CONDITIONS]
        if matched_meds:
            requires_clinical_referral = True
            warnings.append(f"Medical conditions flagged ({', '.join(matched_meds)}). Please consult a certified clinical dietitian before making significant dietary changes.")

        # Extreme BMI warning
        bmi = user_profile.bmi or 22.0
        if bmi < 16.0:
            requires_clinical_referral = True
            warnings.append("Severe underweight detected (BMI < 16.0). Professional medical guidance is required.")
        elif bmi > 38.0:
            warnings.append("High BMI detected. Recommendations emphasize gradual metabolic optimization.")

        # Extreme Calorie bounds check
        t_cal = user_profile.target_calories or 2000.0
        if t_cal < 1200.0:
            warnings.append("Calorie target adjusted upward to minimum safe floor of 1200 kcal/day.")
        elif t_cal > 4000.0:
            warnings.append("High calorie target flagged (> 4000 kcal/day). Ensure adequate hydration and sodium balance.")

        return {
            "is_safe_for_recommendation": True,
            "requires_clinical_referral": requires_clinical_referral,
            "safety_warnings": warnings,
            "medical_disclaimer": disclaimer
        }

    def filter_safe_foods(self, food_items, allergies=[], dietary_preference="vegetarian"):
        """Filters out foods that trigger user allergies or violate dietary restrictions."""
        user_allergies = set([a.lower() for a in (allergies or [])])
        safe_foods = []

        for food in food_items:
            # Check allergens
            food_allergens = set([a.lower() for a in (food.allergens or [])])
            if user_allergies.intersection(food_allergens):
                continue

            # Check dietary preference
            diet = dietary_preference.lower()
            if diet == "vegan" and food.dietary_type != "vegan":
                continue
            elif diet == "vegetarian" and food.dietary_type not in ["vegetarian", "vegan"]:
                continue
            elif diet == "eggetarian" and food.dietary_type not in ["vegetarian", "vegan", "eggetarian"]:
                continue

            safe_foods.append(food)

        return safe_foods

safety_layer = SafetyGuardrails()
