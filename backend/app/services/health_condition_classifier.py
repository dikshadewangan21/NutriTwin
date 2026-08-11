from app.services.health_condition_rules import health_condition_rules

class HealthConditionClassifier:
    """
    Classifies user health profile and selected conditions into a structured
    Nutrition Pathway (e.g. Diabetes-Aware Pathway, Heart-Healthy Pathway).
    Provides conflict resolution for multi-condition profiles.
    """
    HIGH_RISK_THERAPEUTIC_CONDITIONS = ["kidney_condition", "liver_condition", "heart_condition"]

    def classify_user_pathway(self, selected_conditions, workout_type="Gym", fitness_goal="weight_loss"):
        """Maps user profile & conditions to a Nutrition Pathway string and detects clinical referral flags."""
        conds = [c.lower() for c in (selected_conditions or []) if c.lower() != "none"]
        
        has_high_risk = any(c in self.HIGH_RISK_THERAPEUTIC_CONDITIONS for c in conds)

        pathway_parts = []
        if "diabetes" in conds or "prediabetes" in conds:
            pathway_parts.append("Diabetes-Aware")
        if "hypertension" in conds or "heart_condition" in conds:
            pathway_parts.append("Heart-Healthy Sodium-Conscious")
        if "high_cholesterol" in conds:
            pathway_parts.append("Lipid-Aware")
        if "pcos" in conds:
            pathway_parts.append("PCOS-Aware")
        if "anemia" in conds:
            pathway_parts.append("Iron-Aware")

        # Include workout orientation
        is_active_gym = any(term in workout_type.lower() for term in ["gym", "strength", "crossfit", "heavy"])
        if is_active_gym:
            pathway_parts.append("Strength Training")

        if not pathway_parts:
            pathway_name = "General Wellness & Metabolic Optimization Pathway"
        else:
            pathway_name = " + ".join(pathway_parts) + " Nutrition Pathway"

        aggregated_constraints = health_condition_rules.aggregate_condition_constraints(conds)

        clinical_notice = None
        if has_high_risk:
            clinical_notice = "You selected a complex health condition (e.g., Kidney, Liver, or Cardiac condition). NutriTwin provides general wellness guidance; please review your meal plan with your attending clinician or registered dietitian."

        return {
            "classified_pathway": pathway_name,
            "selected_conditions": conds,
            "is_multi_condition": len(conds) > 1,
            "has_high_risk_condition": has_high_risk,
            "clinical_referral_needed": has_high_risk,
            "clinical_notice": clinical_notice,
            "aggregated_constraints": aggregated_constraints
        }

health_condition_classifier = HealthConditionClassifier()
