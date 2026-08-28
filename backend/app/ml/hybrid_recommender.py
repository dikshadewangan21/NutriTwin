import numpy as np

class HybridRecommendationEngine:
    def __init__(self):
        pass

    def compute_macro_fit(self, food_item, target_macros):
        """Calculate nutritional similarity fit score [0.0 - 1.0]."""
        t_cal = max(target_macros.get("calories", 500), 1)
        t_pro = max(target_macros.get("protein_g", 20), 1)
        t_carb = max(target_macros.get("carbs_g", 60), 1)
        t_fat = max(target_macros.get("fat_g", 15), 1)
        
        target_vec = np.array([1.0, t_pro/t_cal, t_carb/t_cal, t_fat/t_cal])
        
        f_cal = food_item.calories
        f_pro = food_item.protein_g
        f_carb = food_item.carbs_g
        f_fat = food_item.fat_g
        
        food_vec = np.array([f_cal/t_cal, f_pro/t_cal, f_carb/t_cal, f_fat/t_cal])
        
        norm_t = np.linalg.norm(target_vec)
        norm_f = np.linalg.norm(food_vec)
        if norm_t == 0 or norm_f == 0:
            return 0.5
        cosine_sim = float(np.dot(target_vec, food_vec) / (norm_t * norm_f))
        
        cal_ratio = min(f_cal / t_cal, 1.5)
        cal_diff_penalty = abs(1.0 - cal_ratio) * 0.3
        
        return max(0.0, min(1.0, cosine_sim - cal_diff_penalty))

    def compute_health_condition_fit(self, food_item, health_constraints):
        """Calculate health condition compatibility score [0.0 - 1.0]."""
        if not health_constraints:
            return 1.0

        score = 1.0
        max_gi = health_constraints.get("max_glycemic_index", "High")
        
        # Glycemic Index check for Diabetes/Prediabetes/PCOS
        if max_gi == "Medium" and getattr(food_item, "glycemic_index", "Medium") == "High":
            score -= 0.4
            
        # Saturated Fat check for Cholesterol
        max_sat = health_constraints.get("max_saturated_fat_g", 25.0)
        if food_item.fat_g > max_sat:
            score -= 0.3

        # Fiber reward
        min_fiber = health_constraints.get("min_daily_fiber_g", 25.0)
        if food_item.fiber_g >= (min_fiber / 4.0):
            score += 0.15

        return max(0.1, min(1.0, score))

    def compute_preference_score(self, food_item, user_profile, user_feedback_history):
        """Compute score based on user likes, dislikes, ratings, and past skips."""
        name_lower = food_item.name.lower()
        liked = [x.lower() for x in (user_profile.liked_foods or [])]
        disliked = [x.lower() for x in (user_profile.disliked_foods or [])]
        
        if any(d in name_lower for d in disliked):
            return 0.05
            
        score = 0.5
        if any(l in name_lower for l in liked):
            score += 0.35
            
        food_feedback = [f for f in user_feedback_history if f.get("food_id") == food_item.id]
        if food_feedback:
            skips = sum(1 for f in food_feedback if f.get("action_type") == "skipped")
            consumed = sum(1 for f in food_feedback if f.get("action_type") == "consumed")
            ratings = [f.get("rating") for f in food_feedback if f.get("rating") is not None]
            
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
                score += (avg_rating - 3.0) * 0.1
                
            if skips > 0:
                score -= min(0.35, skips * 0.12)
            if consumed > 0:
                score += min(0.2, consumed * 0.05)
                
        return max(0.0, min(1.0, score))

    def compute_meal_type_suitability(self, food_item, meal_type: str) -> float:
        """Calculate meal slot suitability score [0.0 - 1.0]."""
        cat = getattr(food_item, "category", "lunch").lower()
        slot = (meal_type or "lunch").lower()

        if cat == slot:
            return 1.0

        # Meal slot cross-compatibility
        if slot == "breakfast":
            if cat in ["breakfast", "snack", "beverage"]:
                return 0.85
            return 0.15  # Heavily penalize main courses for breakfast
        elif slot in ["lunch", "dinner"]:
            if cat in ["lunch", "dinner", "main_course"]:
                return 1.0
            elif cat in ["breakfast", "snack"]:
                return 0.35
            return 0.50
        elif slot == "snack":
            if cat in ["snack", "beverage"]:
                return 1.0
            elif cat == "breakfast":
                return 0.70
            return 0.20  # Heavily penalize heavy main courses for snack

        return 0.50

    def compute_budget_fit(self, food_item, user_profile, meal_type):
        """Calculate budget alignment score."""
        daily_budget = user_profile.daily_budget_inr or 300.0
        alloc_map = {"breakfast": 0.20, "pre_workout": 0.10, "post_workout": 0.15, "lunch": 0.30, "dinner": 0.30, "snack": 0.10}
        target_meal_budget = daily_budget * alloc_map.get(meal_type, 0.25)
        
        cost = food_item.approx_cost_inr
        if cost <= target_meal_budget:
            return 1.0
        else:
            over = cost - target_meal_budget
            return max(0.2, 1.0 - (over / target_meal_budget))

    def compute_diversity_score(self, food_item, recently_selected_ids):
        if food_item.id in recently_selected_ids:
            count = recently_selected_ids.count(food_item.id)
            return max(0.1, 1.0 - (count * 0.4))
        return 1.0

    def score_and_rank_foods(self, food_items, user_profile, target_macros, meal_type, user_feedback_history=[], recent_food_ids=[], health_constraints={}):
        """Score and rank candidate food items including health condition compatibility and meal type suitability."""
        scored_foods = []
        
        user_diet = user_profile.dietary_preference or "vegetarian"
        user_allergies = set([a.lower() for a in (user_profile.allergies or [])])
        
        for food in food_items:
            # Allergen filter
            food_allergens = set([a.lower() for a in (food.allergens or [])])
            if user_allergies.intersection(food_allergens):
                continue
                
            # Dietary preference filter
            if user_diet == "vegan" and food.dietary_type != "vegan":
                continue
            elif user_diet == "vegetarian" and food.dietary_type not in ["vegetarian", "vegan"]:
                continue
            elif user_diet == "eggetarian" and food.dietary_type not in ["vegetarian", "vegan", "eggetarian"]:
                continue

            # Compute individual sub-scores
            macro_score = self.compute_macro_fit(food, target_macros)
            health_score = self.compute_health_condition_fit(food, health_constraints)
            meal_suitability = self.compute_meal_type_suitability(food, meal_type)
            pref_score = self.compute_preference_score(food, user_profile, user_feedback_history)
            budget_score = self.compute_budget_fit(food, user_profile, meal_type)
            diversity_score = self.compute_diversity_score(food, recent_food_ids)
            
            region_boost = 1.0 if (food.region == "All India" or food.region == user_profile.location_region) else 0.85

            # Hybrid Score Combination including Meal Type Suitability
            final_score = (
                0.25 * macro_score +
                0.20 * health_score +
                0.25 * meal_suitability +
                0.15 * pref_score +
                0.05 * budget_score +
                0.05 * diversity_score +
                0.05 * region_boost
            )
            
            scored_foods.append({
                "food": food,
                "score": round(float(final_score), 4),
                "breakdown": {
                    "macro_fit": round(float(macro_score), 3),
                    "health_condition_fit": round(float(health_score), 3),
                    "meal_type_suitability": round(float(meal_suitability), 3),
                    "preference_fit": round(float(pref_score), 3),
                    "budget_fit": round(float(budget_score), 3),
                    "diversity_score": round(float(diversity_score), 3),
                    "region_boost": round(float(region_boost), 3)
                }
            })

        scored_foods.sort(key=lambda x: x["score"], reverse=True)
        return scored_foods

hybrid_recommender = HybridRecommendationEngine()
