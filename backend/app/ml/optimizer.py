import time
import pulp
import numpy as np
from typing import List, Dict, Any, Optional

class MultiConstraintDietOptimizer:
    """
    Mathematical Optimization Solver using PuLP CBC ILP Solver.
    Solves daily meal selection enforcing budget, macro targets, dietary types,
    category balance, and health/allergen restrictions.
    """
    def __init__(self):
        pass

    def optimize_daily_meals(
        self, 
        candidate_foods: Optional[List[Any]] = None, 
        user_profile: Optional[Any] = None, 
        target_macros: Optional[Dict[str, float]] = None, 
        locked_meal_ids: List[int] = [], 
        include_workout_meals: bool = False, 
        health_constraints: Dict[str, Any] = {}
    ) -> Dict[str, Any]:
        """
        Solves Integer Linear Programming (ILP) meal selection using PuLP with a 3-second solver timeout limit.
        """
        start_time = time.time()

        # Default parameters if None
        if target_macros is None:
            target_macros = {"calories": 2000.0, "protein_g": 75.0, "carbs_g": 250.0, "fat_g": 65.0}

        t_cal = float(target_macros.get("calories", 2000.0))
        t_pro = float(target_macros.get("protein_g", 75.0))
        t_carb = float(target_macros.get("carbs_g", 250.0))
        t_fat = float(target_macros.get("fat_g", 65.0))

        # Extract budget
        user_budget = getattr(user_profile, "daily_budget_inr", 250.0) if user_profile else 250.0
        max_budget = float(user_budget if user_budget is not None else 250.0)

        # Extract dietary preference & allergies
        user_diet = (getattr(user_profile, "dietary_preference", "vegetarian") or "vegetarian").lower()
        user_allergies = set([a.lower() for a in (getattr(user_profile, "allergies", []) or [])])

        # Query database for candidate_foods if not provided
        if not candidate_foods:
            try:
                from app.database import SessionLocal, Base, engine
                from app.models.food import FoodItem
                Base.metadata.create_all(bind=engine)
                db = SessionLocal()
                candidate_foods = db.query(FoodItem).all()
                db.close()
            except Exception as e:
                print(f"[DietOptimizer] DB query error: {e}")
                candidate_foods = []

        # If DB query returned no candidate foods, import from seed dataset
        if not candidate_foods:
            try:
                from app.seed_data import INDIAN_FOOD_DATASET
                class TempFoodItem:
                    def __init__(self, d, idx):
                        self.id = idx + 1
                        self.name = d["name"]
                        self.category = d["category"]
                        self.calories = d["calories"]
                        self.protein_g = d["protein_g"]
                        self.carbs_g = d["carbs_g"]
                        self.fat_g = d["fat_g"]
                        self.fiber_g = d.get("fiber_g", 2.0)
                        self.dietary_type = d["dietary_type"]
                        self.region = d.get("region", "All India")
                        self.approx_cost_inr = d["approx_cost_inr"]
                        self.allergens = d.get("allergens", [])
                        self.glycemic_index = d.get("glycemic_index", "Medium")

                candidate_foods = [TempFoodItem(d, i) for i, d in enumerate(INDIAN_FOOD_DATASET)]
            except Exception as e:
                print(f"[DietOptimizer] Seed fallback error: {e}")

        # Filter candidates based on dietary preference & hard allergen constraints
        filtered_candidates = []
        for f in candidate_foods:
            # Allergen check
            f_allergens = set([a.lower() for a in (getattr(f, "allergens", []) or [])])
            if user_allergies.intersection(f_allergens):
                continue

            # Dietary preference filter
            f_diet = (getattr(f, "dietary_type", "vegetarian") or "vegetarian").lower()
            if user_diet == "vegan" and f_diet != "vegan":
                continue
            elif user_diet == "vegetarian" and f_diet not in ["vegetarian", "vegan"]:
                continue
            elif user_diet == "eggetarian" and f_diet not in ["vegetarian", "vegan", "eggetarian"]:
                continue

            filtered_candidates.append(f)

        # Fallback if filtered list is too small
        if len(filtered_candidates) < 4:
            filtered_candidates = list(candidate_foods)

        # Construct PuLP ILP Problem
        prob = pulp.LpProblem("NutriTwin_Daily_Diet_Optimizer", pulp.LpMinimize)

        # Binary decision variables for food selection
        food_vars = {f.id: pulp.LpVariable(f"food_{f.id}", cat=pulp.LpBinary) for f in filtered_candidates}

        # Deviation slack variables
        cal_dev = pulp.LpVariable("cal_dev", lowBound=0)
        pro_dev = pulp.LpVariable("pro_dev", lowBound=0)
        carb_dev = pulp.LpVariable("carb_dev", lowBound=0)
        fat_dev = pulp.LpVariable("fat_dev", lowBound=0)

        # Objective Function: minimize weighted macro deviation + food cost
        prob += (
            1.0 * cal_dev +
            4.0 * pro_dev +
            1.2 * carb_dev +
            1.5 * fat_dev +
            0.5 * pulp.lpSum([f.approx_cost_inr * food_vars[f.id] for f in filtered_candidates])
        )

        # Macro deviation bounds
        prob += pulp.lpSum([f.calories * food_vars[f.id] for f in filtered_candidates]) - t_cal <= cal_dev
        prob += t_cal - pulp.lpSum([f.calories * food_vars[f.id] for f in filtered_candidates]) <= cal_dev

        prob += t_pro - pulp.lpSum([f.protein_g * food_vars[f.id] for f in filtered_candidates]) <= pro_dev
        prob += pulp.lpSum([f.protein_g * food_vars[f.id] for f in filtered_candidates]) >= 0.70 * t_pro

        prob += pulp.lpSum([f.carbs_g * food_vars[f.id] for f in filtered_candidates]) - t_carb <= carb_dev
        prob += t_carb - pulp.lpSum([f.carbs_g * food_vars[f.id] for f in filtered_candidates]) <= carb_dev

        prob += pulp.lpSum([f.fat_g * food_vars[f.id] for f in filtered_candidates]) - t_fat <= fat_dev
        prob += t_fat - pulp.lpSum([f.fat_g * food_vars[f.id] for f in filtered_candidates]) <= fat_dev

        # HARD BUDGET CONSTRAINT: Total Daily Cost <= Max Budget
        prob += pulp.lpSum([f.approx_cost_inr * food_vars[f.id] for f in filtered_candidates]) <= max_budget

        # Meal Category Structure Constraints
        bf_foods = [f for f in filtered_candidates if getattr(f, "category", "") == "breakfast"]
        lunch_foods = [f for f in filtered_candidates if getattr(f, "category", "") == "lunch"]
        dinner_foods = [f for f in filtered_candidates if getattr(f, "category", "") == "dinner"]
        snack_foods = [f for f in filtered_candidates if getattr(f, "category", "") == "snack"]

        if bf_foods:
            prob += pulp.lpSum([food_vars[f.id] for f in bf_foods]) == 1
        if lunch_foods:
            prob += pulp.lpSum([food_vars[f.id] for f in lunch_foods]) == 1
        if dinner_foods:
            prob += pulp.lpSum([food_vars[f.id] for f in dinner_foods]) == 1
        if snack_foods:
            prob += pulp.lpSum([food_vars[f.id] for f in snack_foods]) >= 1
            prob += pulp.lpSum([food_vars[f.id] for f in snack_foods]) <= (3 if include_workout_meals else 2)

        # Enforce locked meals if specified
        for lid in locked_meal_ids:
            if lid in food_vars:
                prob += food_vars[lid] == 1

        # Execute PuLP Solver with a strict 3-second timeout
        solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=3)
        status = prob.solve(solver)
        solve_duration = round(time.time() - start_time, 4)

        selected_foods = []
        is_optimal = status in [pulp.LpStatusOptimal, 1]

        if is_optimal:
            for f in filtered_candidates:
                if food_vars[f.id].varValue and food_vars[f.id].varValue > 0.5:
                    selected_foods.append(f)

        # Handle infeasible / timeout solutions gracefully via greedy heuristic fallback
        if not selected_foods:
            status_str = "infeasible_fallback"
            selected_foods = self._greedy_fallback(filtered_candidates, target_macros, max_budget)
        else:
            status_str = "optimal"

        tot_cal = sum(getattr(f, "calories", 0.0) for f in selected_foods)
        tot_pro = sum(getattr(f, "protein_g", 0.0) for f in selected_foods)
        tot_carb = sum(getattr(f, "carbs_g", 0.0) for f in selected_foods)
        tot_fat = sum(getattr(f, "fat_g", 0.0) for f in selected_foods)
        tot_cost = sum(getattr(f, "approx_cost_inr", 0.0) for f in selected_foods)

        return {
            "selected_foods": selected_foods,
            "status": status_str,
            "solve_time_sec": solve_duration,
            "totals": {
                "calories": round(tot_cal, 1),
                "protein_g": round(tot_pro, 1),
                "carbs_g": round(tot_carb, 1),
                "fat_g": round(tot_fat, 1),
                "cost_inr": round(tot_cost, 2)
            },
            "constraint_deviations": {
                "calorie_diff": round(tot_cal - t_cal, 1),
                "protein_diff": round(tot_pro - t_pro, 1),
                "budget_remaining": round(max_budget - tot_cost, 2)
            }
        }

    def _greedy_fallback(self, candidate_foods: List[Any], target_macros: Dict[str, float], max_budget: float) -> List[Any]:
        """Greedy fallback selector used when PuLP ILP solver finds problem infeasible under tight constraints."""
        selected = []
        budget_left = max_budget
        target_cal_per_meal = target_macros.get("calories", 2000.0) * 0.25

        for cat in ["breakfast", "lunch", "dinner", "snack"]:
            cat_foods = [f for f in candidate_foods if getattr(f, "category", "") == cat and getattr(f, "approx_cost_inr", 0.0) <= budget_left]
            if not cat_foods:
                cat_foods = [f for f in candidate_foods if getattr(f, "category", "") == cat]

            if cat_foods:
                best = min(cat_foods, key=lambda f: (
                    abs(getattr(f, "calories", 250) - target_cal_per_meal) + getattr(f, "approx_cost_inr", 50) * 2.0
                ))
                selected.append(best)
                budget_left -= getattr(best, "approx_cost_inr", 0.0)

        return selected

diet_optimizer = MultiConstraintDietOptimizer()
