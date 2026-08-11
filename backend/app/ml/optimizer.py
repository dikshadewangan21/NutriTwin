import pulp
import numpy as np

class MultiConstraintDietOptimizer:
    def __init__(self):
        pass

    def optimize_daily_meals(self, candidate_foods, user_profile, target_macros, locked_meal_ids=[], include_workout_meals=False, health_constraints={}):
        """
        Solves integer linear programming (ILP) optimization using PuLP to select
        optimal meal combination enforcing total daily food cost <= user budget.
        """
        prob = pulp.LpProblem("NutriTwin_Daily_Diet_Optimizer", pulp.LpMinimize)
        
        food_vars = {f.id: pulp.LpVariable(f"food_{f.id}", cat=pulp.LpBinary) for f in candidate_foods}
        
        cal_dev = pulp.LpVariable("cal_dev", lowBound=0)
        pro_dev = pulp.LpVariable("pro_dev", lowBound=0)
        carb_dev = pulp.LpVariable("carb_dev", lowBound=0)
        fat_dev = pulp.LpVariable("fat_dev", lowBound=0)
        
        t_cal = target_macros.get("calories", 2000.0)
        t_pro = target_macros.get("protein_g", 75.0)
        t_carb = target_macros.get("carbs_g", 250.0)
        t_fat = target_macros.get("fat_g", 65.0)
        max_budget = user_profile.daily_budget_inr or 250.0

        # Objective function: minimize deviation + cost
        prob += (
            1.0 * cal_dev +
            4.0 * pro_dev +
            1.2 * carb_dev +
            1.5 * fat_dev +
            0.5 * pulp.lpSum([f.approx_cost_inr * food_vars[f.id] for f in candidate_foods])
        )

        # Macro constraints
        prob += pulp.lpSum([f.calories * food_vars[f.id] for f in candidate_foods]) - t_cal <= cal_dev
        prob += t_cal - pulp.lpSum([f.calories * food_vars[f.id] for f in candidate_foods]) <= cal_dev
        
        prob += t_pro - pulp.lpSum([f.protein_g * food_vars[f.id] for f in candidate_foods]) <= pro_dev
        prob += pulp.lpSum([f.protein_g * food_vars[f.id] for f in candidate_foods]) >= 0.85 * t_pro
        
        prob += pulp.lpSum([f.carbs_g * food_vars[f.id] for f in candidate_foods]) - t_carb <= carb_dev
        prob += t_carb - pulp.lpSum([f.carbs_g * food_vars[f.id] for f in candidate_foods]) <= carb_dev

        prob += pulp.lpSum([f.fat_g * food_vars[f.id] for f in candidate_foods]) - t_fat <= fat_dev
        prob += t_fat - pulp.lpSum([f.fat_g * food_vars[f.id] for f in candidate_foods]) <= fat_dev

        # HARD BUDGET CONSTRAINT: Total Daily Food Cost <= User Budget
        prob += pulp.lpSum([f.approx_cost_inr * food_vars[f.id] for f in candidate_foods]) <= max_budget

        # Structure constraints
        bf_foods = [f for f in candidate_foods if f.category == "breakfast"]
        lunch_foods = [f for f in candidate_foods if f.category == "lunch"]
        dinner_foods = [f for f in candidate_foods if f.category == "dinner"]
        snack_foods = [f for f in candidate_foods if f.category == "snack"]

        if bf_foods:
            prob += pulp.lpSum([food_vars[f.id] for f in bf_foods]) == 1
        if lunch_foods:
            prob += pulp.lpSum([food_vars[f.id] for f in lunch_foods]) == 1
        if dinner_foods:
            prob += pulp.lpSum([food_vars[f.id] for f in dinner_foods]) == 1
        if snack_foods:
            prob += pulp.lpSum([food_vars[f.id] for f in snack_foods]) >= 1
            prob += pulp.lpSum([food_vars[f.id] for f in snack_foods]) <= (3 if include_workout_meals else 2)

        # Enforce locked meals if any
        for lid in locked_meal_ids:
            if lid in food_vars:
                prob += food_vars[lid] == 1

        # Solve ILP
        solver = pulp.PULP_CBC_CMD(msg=0)
        status = prob.solve(solver)

        selected_foods = []
        if status == pulp.LpStatusOptimal or status == 1:
            for f in candidate_foods:
                if food_vars[f.id].varValue and food_vars[f.id].varValue > 0.5:
                    selected_foods.append(f)
        else:
            selected_foods = self._greedy_fallback(candidate_foods, target_macros, max_budget)

        tot_cal = sum(f.calories for f in selected_foods)
        tot_pro = sum(f.protein_g for f in selected_foods)
        tot_carb = sum(f.carbs_g for f in selected_foods)
        tot_fat = sum(f.fat_g for f in selected_foods)
        tot_cost = sum(f.approx_cost_inr for f in selected_foods)

        return {
            "selected_foods": selected_foods,
            "status": "optimal" if status in [pulp.LpStatusOptimal, 1] else "heuristic_fallback",
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

    def _greedy_fallback(self, candidate_foods, target_macros, max_budget):
        selected = []
        budget_left = max_budget
        for cat in ["breakfast", "lunch", "dinner", "snack"]:
            cat_foods = [f for f in candidate_foods if f.category == cat and f.approx_cost_inr <= budget_left]
            if cat_foods:
                best = min(cat_foods, key=lambda f: abs(f.calories - target_macros.get("calories", 2000)*0.25))
                selected.append(best)
                budget_left -= best.approx_cost_inr
        return selected

diet_optimizer = MultiConstraintDietOptimizer()
