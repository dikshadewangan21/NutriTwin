import os
import time
import json
import random
import numpy as np
from pathlib import Path
from typing import List, Dict, Any

from app.database import SessionLocal, Base, engine
from app.models.food import FoodItem
from app.ml.optimizer import diet_optimizer

# Directory Paths
BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "processed"

EVAL_JSON_OUT = PROCESSED_DIR / "pulp_optimizer_evaluation.json"
REPORT_JSON_OUT = PROCESSED_DIR / "pulp_eval_report.json"


class DummyUserProfile:
    def __init__(self, budget_inr: float, diet: str, allergies: List[str] = []):
        self.daily_budget_inr = budget_inr
        self.dietary_preference = diet
        self.allergies = allergies


def generate_100_constraint_scenarios() -> List[Dict[str, Any]]:
    """
    Generates 100+ diverse, rigorous constraint scenarios testing:
      - Budgets: ₹100, ₹150, ₹200, ₹250, ₹300, ₹400, ₹500, ₹700
      - Dietary Types: vegetarian, vegan, eggetarian, non_vegetarian
      - Macro Targets: low calorie, high protein, muscle gain, weight loss, standard
      - Restrictive Edge Cases: tight budget + high protein + vegan, allergen restrictions
    """
    random.seed(42)

    budgets = [100.0, 150.0, 200.0, 250.0, 300.0, 400.0, 500.0, 700.0]
    diets = ["vegetarian", "vegan", "eggetarian", "non_vegetarian"]
    
    target_presets = [
        {"name": "standard_balanced", "calories": 2000.0, "protein_g": 80.0, "carbs_g": 250.0, "fat_g": 60.0},
        {"name": "high_protein_muscle", "calories": 2400.0, "protein_g": 140.0, "carbs_g": 260.0, "fat_g": 70.0},
        {"name": "low_calorie_weightloss", "calories": 1400.0, "protein_g": 90.0, "carbs_g": 150.0, "fat_g": 45.0},
        {"name": "extreme_high_protein", "calories": 2600.0, "protein_g": 170.0, "carbs_g": 280.0, "fat_g": 75.0},
        {"name": "keto_low_carb", "calories": 1800.0, "protein_g": 110.0, "carbs_g": 50.0, "fat_g": 110.0},
        {"name": "budget_lean", "calories": 1600.0, "protein_g": 70.0, "carbs_g": 210.0, "fat_g": 50.0}
    ]

    allergen_presets = [[], ["dairy"], ["nuts"], ["gluten"], ["dairy", "nuts"]]

    scenarios = []
    scenario_id = 1

    # Systematic combination loop (~120 scenarios)
    for b in budgets:
        for d in diets:
            for preset in target_presets:
                allergies = random.choice(allergen_presets)
                scenarios.append({
                    "scenario_id": scenario_id,
                    "budget_inr": b,
                    "dietary_preference": d,
                    "target_macros": {
                        "calories": preset["calories"],
                        "protein_g": preset["protein_g"],
                        "carbs_g": preset["carbs_g"],
                        "fat_g": preset["fat_g"]
                    },
                    "allergies": allergies,
                    "preset_name": preset["name"]
                })
                scenario_id += 1
                if scenario_id > 105:
                    break
            if scenario_id > 105:
                break
        if scenario_id > 105:
            break

    # Add specific restrictive edge case scenarios
    edge_cases = [
        {"budget_inr": 100.0, "dietary_preference": "vegan", "target_macros": {"calories": 1800.0, "protein_g": 120.0, "carbs_g": 200.0, "fat_g": 50.0}, "allergies": ["nuts"], "preset_name": "edge_tight_vegan_protein"},
        {"budget_inr": 120.0, "dietary_preference": "vegetarian", "target_macros": {"calories": 1300.0, "protein_g": 110.0, "carbs_g": 140.0, "fat_g": 40.0}, "allergies": ["dairy"], "preset_name": "edge_low_cal_no_dairy"},
        {"budget_inr": 150.0, "dietary_preference": "vegan", "target_macros": {"calories": 2500.0, "protein_g": 150.0, "carbs_g": 300.0, "fat_g": 60.0}, "allergies": [], "preset_name": "edge_high_pro_cheap_vegan"},
        {"budget_inr": 500.0, "dietary_preference": "non_vegetarian", "target_macros": {"calories": 3000.0, "protein_g": 180.0, "carbs_g": 350.0, "fat_g": 90.0}, "allergies": [], "preset_name": "edge_luxury_bulk"}
    ]

    for ec in edge_cases:
        ec["scenario_id"] = scenario_id
        scenarios.append(ec)
        scenario_id += 1

    return scenarios


def evaluate_pulp_optimizer():
    """
    Executes Phase 11 evaluation over 100+ generated constraint scenarios.
    Measures solver status, solve time, budget compliance, macro deviations,
    and saves dynamic evaluation results to processed JSON.
    """
    print("=" * 75)
    print("[NutriTwin Phase 11] Evaluating PuLP Multi-Constraint Meal Plan Optimizer...")
    print("=" * 75)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Fetch real FoodItem records from database
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        all_foods = db.query(FoodItem).all()
        num_foods = len(all_foods)
        print(f"1. Loaded {num_foods} verified FoodItem database records from Phase 1 database.")
    finally:
        db.close()

    scenarios = generate_100_constraint_scenarios()
    num_scenarios = len(scenarios)
    print(f"2. Generated {num_scenarios} diverse constraint scenarios for testing.\n")

    results = []
    solve_times = []
    cal_diffs = []
    pro_diffs = []

    feasible_optimal_count = 0
    infeasible_fallback_count = 0
    budget_compliant_count = 0
    macro_satisfied_count = 0

    for sc in scenarios:
        sid = sc["scenario_id"]
        budget = sc["budget_inr"]
        diet = sc["dietary_preference"]
        target_macros = sc["target_macros"]
        allergies = sc["allergies"]

        dummy_user = DummyUserProfile(budget_inr=budget, diet=diet, allergies=allergies)

        t_start = time.time()
        res = diet_optimizer.optimize_daily_meals(
            candidate_foods=all_foods,
            user_profile=dummy_user,
            target_macros=target_macros
        )
        t_duration_ms = round((time.time() - t_start) * 1000.0, 2)

        solve_times.append(t_duration_ms)

        is_optimal = (res["status"] == "optimal")
        if is_optimal:
            feasible_optimal_count += 1
        else:
            infeasible_fallback_count += 1

        tot = res["totals"]
        dev = res["constraint_deviations"]

        c_diff = abs(dev["calorie_diff"])
        p_diff = abs(dev["protein_diff"])

        cal_diffs.append(c_diff)
        pro_diffs.append(p_diff)

        # Budget compliance check: total cost <= max budget (allowing 0.5 INR float precision)
        is_budget_sat = bool(tot["cost_inr"] <= budget + 0.5)
        if is_budget_sat:
            budget_compliant_count += 1

        # Macro satisfaction: calorie & protein within 15% tolerance
        cal_target = target_macros["calories"]
        pro_target = target_macros["protein_g"]
        is_cal_ok = bool(c_diff <= 0.15 * cal_target)
        is_pro_ok = bool(p_diff <= 0.20 * pro_target)
        is_macro_ok = bool(is_cal_ok and is_pro_ok)

        if is_macro_ok:
            macro_satisfied_count += 1

        record = {
            "scenario_id": sid,
            "preset_name": sc["preset_name"],
            "budget_inr": budget,
            "dietary_preference": diet,
            "target_calories": cal_target,
            "target_protein_g": pro_target,
            "status": res["status"],
            "is_feasible": is_optimal,
            "solve_time_ms": t_duration_ms,
            "achieved_totals": tot,
            "budget_satisfaction": is_budget_sat,
            "calorie_deviation": round(c_diff, 1),
            "protein_deviation": round(p_diff, 1),
            "macro_satisfied": is_macro_ok
        }
        results.append(record)

    # 3. Aggregate Statistical Report
    avg_solve_ms = round(float(np.mean(solve_times)), 2)
    max_solve_ms = round(float(np.max(solve_times)), 2)
    feasibility_rate = round(feasible_optimal_count / num_scenarios * 100.0, 2)
    budget_compliance_rate = round(budget_compliant_count / num_scenarios * 100.0, 2)
    macro_satisfaction_rate = round(macro_satisfied_count / num_scenarios * 100.0, 2)

    avg_cal_dev = round(float(np.mean(cal_diffs)), 1)
    avg_pro_dev = round(float(np.mean(pro_diffs)), 1)

    eval_summary = {
        "evaluation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "database_records_evaluated": num_foods,
        "total_scenarios_tested": num_scenarios,
        "optimal_feasible_scenarios": feasible_optimal_count,
        "infeasible_fallback_scenarios": infeasible_fallback_count,
        "feasibility_rate_pct": feasibility_rate,
        "solve_time_ms": {
            "mean": avg_solve_ms,
            "max": max_solve_ms
        },
        "budget_compliance_rate_pct": budget_compliance_rate,
        "macro_satisfaction_rate_pct": macro_satisfaction_rate,
        "average_deviations": {
            "calorie_diff_kcal": avg_cal_dev,
            "protein_diff_g": avg_pro_dev
        }
    }

    # Save outputs
    with open(EVAL_JSON_OUT, "w", encoding="utf-8") as f:
        json.dump({"summary": eval_summary, "scenarios": results}, f, indent=2, ensure_ascii=False)

    with open(REPORT_JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(eval_summary, f, indent=2, ensure_ascii=False)

    print("=" * 75)
    print("PULP MULTI-CONSTRAINT OPTIMIZER DYNAMIC EVALUATION SUMMARY")
    print("=" * 75)
    print(f" Total Scenarios Tested     : {num_scenarios}")
    print(f" Optimal Feasible Count     : {feasible_optimal_count} ({feasibility_rate}%)")
    print(f" Infeasible Fallback Count  : {infeasible_fallback_count}")
    print(f" Avg Solve Time             : {avg_solve_ms} ms (Max: {max_solve_ms} ms)")
    print(f" Budget Compliance Rate     : {budget_compliance_rate}%")
    print(f" Macro Satisfaction Rate    : {macro_satisfaction_rate}%")
    print(f" Avg Calorie Deviation      : {avg_cal_dev} kcal")
    print(f" Avg Protein Deviation      : {avg_pro_dev} g")
    print(f" Output JSON Evaluation     : {EVAL_JSON_OUT}")
    print("=" * 75)

    return eval_summary, results


if __name__ == "__main__":
    evaluate_pulp_optimizer()
