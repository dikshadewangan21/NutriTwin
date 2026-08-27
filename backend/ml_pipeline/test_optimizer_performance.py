import sys
import time
import pandas as pd
import numpy as np
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.ml.optimizer import diet_optimizer
from app.database import SessionLocal, Base, engine
from app.models.food import FoodItem
from app.seed_data import INDIAN_FOOD_DATASET

PROCESSED_DIR = BASE_DIR / "ml_pipeline" / "processed"
CSV_OUT_FILE = PROCESSED_DIR / "optimizer_results.csv"

class MockUserProfile:
    def __init__(self, budget, diet, allergies):
        self.daily_budget_inr = budget
        self.dietary_preference = diet
        self.allergies = allergies

def seed_db_if_empty():
    """Ensure database has the 63 food items from seed_data.py."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    count = db.query(FoodItem).count()
    if count == 0:
        for item in INDIAN_FOOD_DATASET:
            db_food = FoodItem(**item)
            db.add(db_food)
        db.commit()
        print(f"[TestOptimizer] Seeded DB with {len(INDIAN_FOOD_DATASET)} FoodItems.")
    db.close()

def generate_100_scenarios():
    """Generates 105 distinct, comprehensive optimization scenarios."""
    scenarios = []
    scen_id = 1

    budgets = [150.0, 200.0, 250.0, 300.0, 400.0, 500.0, 600.0]
    dietary_types = ["vegetarian", "vegan", "eggetarian", "non_vegetarian"]

    # 1. Standard Combinations (70 scenarios)
    for b in budgets:
        for d in dietary_types:
            for c in [1600.0, 2200.0]:
                for p in [55.0, 85.0, 110.0]:
                    if scen_id <= 70:
                        scenarios.append({
                            "scenario_id": scen_id,
                            "name": f"Budget ₹{int(b)} - {d.capitalize()} ({int(c)}kcal, {int(p)}g pro)",
                            "budget": b,
                            "diet": d,
                            "calories": c,
                            "protein": p,
                            "carbs": c * 0.50 / 4,
                            "fat": c * 0.25 / 9,
                            "allergies": []
                        })
                        scen_id += 1

    # 2. Allergy & Restriction Scenarios (15 scenarios)
    allergy_combos = [
        ["lactose"], ["gluten"], ["nuts"], ["soy"], ["peanuts"],
        ["lactose", "gluten"], ["nuts", "peanuts"], ["lactose", "soy"],
        ["gluten", "nuts"], ["lactose", "gluten", "nuts"],
        ["gluten", "soy"], ["lactose", "peanuts"], ["gluten", "peanuts"],
        ["lactose", "nuts"], ["soy", "peanuts"]
    ]
    for algs in allergy_combos:
        scenarios.append({
            "scenario_id": scen_id,
            "name": f"Allergy Restriction: {','.join(algs)} (Budget ₹250)",
            "budget": 250.0,
            "diet": "vegetarian",
            "calories": 2000.0,
            "protein": 75.0,
            "carbs": 250.0,
            "fat": 65.0,
            "allergies": algs
        })
        scen_id += 1

    # 3. Budget Variations & Low Calorie / Low Fat (10 scenarios)
    low_scenarios = [
        {"name": "Low Calorie 1200kcal ₹150", "budget": 150.0, "calories": 1200.0, "protein": 50.0, "diet": "vegetarian"},
        {"name": "Low Calorie 1400kcal ₹200", "budget": 200.0, "calories": 1400.0, "protein": 60.0, "diet": "vegan"},
        {"name": "High Protein 120g ₹300", "budget": 300.0, "calories": 2200.0, "protein": 120.0, "diet": "non_vegetarian"},
        {"name": "High Protein 130g ₹500", "budget": 500.0, "calories": 2600.0, "protein": 130.0, "diet": "non_vegetarian"},
        {"name": "Low Fat 25g ₹250", "budget": 250.0, "calories": 1800.0, "protein": 70.0, "diet": "vegetarian"},
        {"name": "High Calorie 3200kcal ₹400", "budget": 400.0, "calories": 3200.0, "protein": 100.0, "diet": "vegetarian"},
        {"name": "Low Budget ₹180 Vegan", "budget": 180.0, "calories": 1900.0, "protein": 65.0, "diet": "vegan"},
        {"name": "Moderate Budget ₹200 Eggetarian", "budget": 200.0, "calories": 2000.0, "protein": 80.0, "diet": "eggetarian"},
        {"name": "High Budget ₹500 Vegan High Calorie", "budget": 500.0, "calories": 2800.0, "protein": 95.0, "diet": "vegan"},
        {"name": "Low Budget ₹150 Eggetarian High Protein", "budget": 150.0, "calories": 2100.0, "protein": 90.0, "diet": "eggetarian"}
    ]

    for ls in low_scenarios:
        scenarios.append({
            "scenario_id": scen_id,
            "name": ls["name"],
            "budget": ls["budget"],
            "diet": ls["diet"],
            "calories": ls["calories"],
            "protein": ls["protein"],
            "carbs": ls["calories"] * 0.50 / 4,
            "fat": ls["calories"] * 0.25 / 9,
            "allergies": []
        })
        scen_id += 1

    # 4. Extreme / Impossible Scenarios (10 scenarios)
    extreme_scenarios = [
        {"name": "Impossible Low Budget ₹50", "budget": 50.0, "calories": 2500.0, "protein": 150.0, "diet": "vegetarian", "algs": []},
        {"name": "Impossible Low Budget ₹80 (Vegan)", "budget": 80.0, "calories": 3000.0, "protein": 140.0, "diet": "vegan", "algs": []},
        {"name": "Ultra High Protein 180g (Vegan)", "budget": 200.0, "calories": 1600.0, "protein": 180.0, "diet": "vegan", "algs": []},
        {"name": "Extreme Allergies (Lactose, Gluten, Nuts, Soy, Peanuts)", "budget": 150.0, "calories": 2200.0, "protein": 90.0, "diet": "vegan", "algs": ["lactose", "gluten", "nuts", "soy", "peanuts"]},
        {"name": "Ultra Low Calorie 800kcal High Protein 120g", "budget": 300.0, "calories": 800.0, "protein": 120.0, "diet": "vegetarian", "algs": []},
        {"name": "Tight Budget ₹100 High Protein 130g", "budget": 100.0, "calories": 2400.0, "protein": 130.0, "diet": "non_vegetarian", "algs": []},
        {"name": "Impossible Budget ₹30", "budget": 30.0, "calories": 2000.0, "protein": 75.0, "diet": "vegan", "algs": []},
        {"name": "Vegan + All Nut Allergies ₹150 Budget", "budget": 150.0, "calories": 2200.0, "protein": 100.0, "diet": "vegan", "algs": ["nuts", "peanuts"]},
        {"name": "High Calorie 3500kcal Low Budget ₹180", "budget": 180.0, "calories": 3500.0, "protein": 110.0, "diet": "vegetarian", "algs": []},
        {"name": "Eggetarian Extreme High Protein 160g ₹150", "budget": 150.0, "calories": 2000.0, "protein": 160.0, "diet": "eggetarian", "algs": []}
    ]

    for ext in extreme_scenarios:
        scenarios.append({
            "scenario_id": scen_id,
            "name": ext["name"],
            "budget": ext["budget"],
            "diet": ext["diet"],
            "calories": ext["calories"],
            "protein": ext["protein"],
            "carbs": ext["calories"] * 0.45 / 4,
            "fat": ext["calories"] * 0.25 / 9,
            "allergies": ext["algs"]
        })
        scen_id += 1

    return scenarios

def run_performance_test():
    """Runs all 100+ constraint scenarios dynamically and exports CSV results."""
    print("=" * 80)
    print("PHASE 11 — RUNNING DIET OPTIMIZER PERFORMANCE TEST (100+ SCENARIOS)")
    print("=" * 80)

    seed_db_if_empty()
    scenarios = generate_100_scenarios()
    print(f"Generated {len(scenarios)} distinct constraint scenarios for PuLP ILP evaluation.\n")

    results = []

    for sc in scenarios:
        user = MockUserProfile(sc["budget"], sc["diet"], sc["allergies"])
        target_macros = {
            "calories": sc["calories"],
            "protein_g": sc["protein"],
            "carbs_g": sc["carbs"],
            "fat_g": sc["fat"]
        }

        start_t = time.time()
        res = diet_optimizer.optimize_daily_meals(
            candidate_foods=None, # Will auto-fetch from DB
            user_profile=user,
            target_macros=target_macros
        )
        duration = round(time.time() - start_t, 4)

        totals = res.get("totals", {})
        status = res.get("status", "unknown")
        is_optimal = (status == "optimal")

        tot_cal = totals.get("calories", 0.0)
        tot_pro = totals.get("protein_g", 0.0)
        tot_carb = totals.get("carbs_g", 0.0)
        tot_fat = totals.get("fat_g", 0.0)
        tot_cost = totals.get("cost_inr", 0.0)

        cal_dev = abs(round(tot_cal - sc["calories"], 1))
        pro_dev = abs(round(tot_pro - sc["protein"], 1))
        budget_satisfied = (tot_cost <= sc["budget"] + 0.01)

        results.append({
            "scenario_id": sc["scenario_id"],
            "scenario_name": sc["name"],
            "budget_inr": sc["budget"],
            "target_calories": sc["calories"],
            "target_protein_g": sc["protein"],
            "dietary_preference": sc["diet"],
            "allergies": ",".join(sc["allergies"]) if sc["allergies"] else "none",
            "status": status,
            "is_feasible": is_optimal,
            "solve_time_sec": duration,
            "total_calories": tot_cal,
            "total_protein_g": tot_pro,
            "total_carbs_g": tot_carb,
            "total_fat_g": tot_fat,
            "total_cost_inr": tot_cost,
            "calorie_deviation": cal_dev,
            "protein_deviation": pro_dev,
            "budget_satisfaction": budget_satisfied
        })

    # Convert to DataFrame
    df = pd.DataFrame(results)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(CSV_OUT_FILE, index=False)

    # Calculate summary metrics
    total_scenarios = len(df)
    optimal_count = len(df[df["status"] == "optimal"])
    fallback_count = len(df[df["status"] != "optimal"])
    avg_solve_time = df["solve_time_sec"].mean()
    max_solve_time = df["solve_time_sec"].max()
    budget_pass_rate = (df["budget_satisfaction"].sum() / total_scenarios) * 100
    avg_cal_dev = df["calorie_deviation"].mean()
    avg_pro_dev = df["protein_deviation"].mean()

    print("=" * 80)
    print("DIET OPTIMIZER PERFORMANCE TEST RESULTS SUMMARY")
    print("=" * 80)
    print(f"Total Scenarios Evaluated  : {total_scenarios}")
    print(f"Optimal ILP Solutions Found: {optimal_count} ({optimal_count/total_scenarios*100:.1f}%)")
    print(f"Infeasible Fallbacks Used  : {fallback_count} ({fallback_count/total_scenarios*100:.1f}%)")
    print(f"Average PuLP Solve Time    : {avg_solve_time:.4f} seconds")
    print(f"Max PuLP Solve Time        : {max_solve_time:.4f} seconds")
    print(f"Budget Satisfaction Rate   : {budget_pass_rate:.1f}%")
    print(f"Average Calorie Deviation  : {avg_cal_dev:.1f} kcal")
    print(f"Average Protein Deviation  : {avg_pro_dev:.1f} g")
    print(f"\nResults CSV exported to   : {CSV_OUT_FILE}")
    print("=" * 80)

    return df

if __name__ == "__main__":
    run_performance_test()
