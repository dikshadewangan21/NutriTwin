import numpy as np

class SmartSubstituteEngine:
    """
    Identifies nutritionally equivalent replacement foods when a user requests a swap
    or dislikes a specific food item.
    """
    def find_substitutes(self, target_food, all_candidate_foods, user_profile, top_k=3):
        """
        Finds top K replacement options with closest nutritional profile and matching dietary bounds.
        """
        user_allergies = set([a.lower() for a in (user_profile.allergies or [])])
        user_diet = user_profile.dietary_preference or "vegetarian"
        
        candidates = []
        for food in all_candidate_foods:
            if food.id == target_food.id or food.category != target_food.category:
                continue

            # Check allergens & dietary preference
            food_allergens = set([a.lower() for a in (food.allergens or [])])
            if user_allergies.intersection(food_allergens):
                continue
                
            if user_diet == "vegan" and food.dietary_type != "vegan":
                continue
            elif user_diet == "vegetarian" and food.dietary_type not in ["vegetarian", "vegan"]:
                continue

            # Calculate nutritional distance (Protein, Calorie, Carbs, Fat similarity)
            cal_diff = abs(food.calories - target_food.calories) / max(1, target_food.calories)
            pro_diff = abs(food.protein_g - target_food.protein_g) / max(1, target_food.protein_g)
            cost_diff = abs(food.approx_cost_inr - target_food.approx_cost_inr) / max(1, target_food.approx_cost_inr)
            
            # Match score (0.0 to 1.0)
            match_score = max(0.1, 1.0 - (0.4 * pro_diff + 0.3 * cal_diff + 0.3 * cost_diff))
            
            # Generate justification
            reason = f"Matches protein ({food.protein_g}g vs {target_food.protein_g}g) and calories ({food.calories} kcal)."
            if food.dietary_type == "vegan" and target_food.dietary_type == "vegetarian":
                reason += " Plant-based dairy-free substitute."

            candidates.append({
                "substitute_food": food,
                "match_score_pct": round(match_score * 100.0, 1),
                "reason": reason,
                "macro_diff": {
                    "calories": round(food.calories - target_food.calories, 1),
                    "protein_g": round(food.protein_g - target_food.protein_g, 1),
                    "cost_inr": round(food.approx_cost_inr - target_food.approx_cost_inr, 2)
                }
            })

        candidates.sort(key=lambda x: x["match_score_pct"], reverse=True)
        return candidates[:top_k]

substitute_engine = SmartSubstituteEngine()
