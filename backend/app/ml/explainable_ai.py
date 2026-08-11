class ExplainableAIEngine:
    """
    SHAP-style Feature Importance Explainer giving human-readable natural language
    and feature breakdowns for every recommendation including Health Pathways.
    """
    def __init__(self):
        pass

    def explain_recommendation(self, food_item, score_item, user_profile, remaining_macros, health_pathway="General Wellness Pathway"):
        """Generates visual feature contribution weights and bulleted natural language justification."""
        bd = score_item.get("breakdown", {})
        macro_fit = bd.get("macro_fit", 0.8)
        health_fit = bd.get("health_condition_fit", 0.9)
        pref_fit = bd.get("preference_fit", 0.7)
        budget_fit = bd.get("budget_fit", 0.9)
        diversity_fit = bd.get("diversity_score", 1.0)
        region_fit = bd.get("region_boost", 1.0)

        total = macro_fit * 0.30 + health_fit * 0.25 + pref_fit * 0.20 + budget_fit * 0.10 + diversity_fit * 0.10 + region_fit * 0.05
        total = max(total, 0.001)

        shap_values = [
            {"feature": "Nutritional Fit (Macros)", "contribution_pct": round((macro_fit * 0.30 / total) * 100, 1), "impact": "positive"},
            {"feature": "Health Pathway Fit", "contribution_pct": round((health_fit * 0.25 / total) * 100, 1), "impact": "positive"},
            {"feature": "User Taste Preferences", "contribution_pct": round((pref_fit * 0.20 / total) * 100, 1), "impact": "positive"},
            {"feature": "Budget Alignment", "contribution_pct": round((budget_fit * 0.10 / total) * 100, 1), "impact": "positive"},
            {"feature": "Meal Variety & Diversity", "contribution_pct": round((diversity_fit * 0.10 / total) * 100, 1), "impact": "positive"},
            {"feature": "Local & Regional Fit", "contribution_pct": round((region_fit * 0.05 / total) * 100, 1), "impact": "positive"}
        ]

        reasons = []
        rem_pro = remaining_macros.get("protein_g", 30)
        if food_item.protein_g >= 12.0 and rem_pro > 15:
            reasons.append(f"Provides {food_item.protein_g}g protein, directly fulfilling your daily target.")
        
        if health_pathway and health_pathway != "General Wellness & Metabolic Optimization Pathway":
            reasons.append(f"Matches your selected '{health_pathway}' bounds.")

        if food_item.approx_cost_inr <= (user_profile.daily_budget_inr or 300) * 0.3:
            reasons.append(f"Fits comfortably within your budget at ₹{food_item.approx_cost_inr} per serving.")

        if food_item.dietary_type == user_profile.dietary_preference:
            reasons.append(f"Matches your exact '{food_item.dietary_type.capitalize()}' food preference.")

        if food_item.region == "All India" or food_item.region == user_profile.location_region:
            reasons.append(f"Uses locally accessible ingredients popular in {user_profile.location_region}.")

        if not reasons:
            reasons.append(f"Satisfies calorie target of {food_item.calories} kcal with balanced nutrients.")

        return {
            "food_id": food_item.id,
            "food_name": food_item.name,
            "overall_recommendation_score": score_item.get("score", 0.85),
            "shap_feature_contributions": shap_values,
            "explanation_bullets": reasons,
            "explainability_model": "SHAP-style Feature Impact Deconstruction (XAI)"
        }

explainable_ai = ExplainableAIEngine()
