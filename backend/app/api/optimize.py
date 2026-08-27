from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
import random

from app.database import get_db
from app.models.user import User, UserProfile
from app.models.food import FoodItem
from app.models.health import UserHealthProfile
from app.models.log import MealPlan, MealPlanItem
from app.schemas.food import FoodItemSchema, PantryInventoryRequest
from app.schemas.recommend import OptimizeMealPlanRequest
from app.api.auth import get_current_user
from app.ml.optimizer import diet_optimizer
from app.services.safety_layer import safety_layer
from app.services.inventory_engine import inventory_engine
from app.services.grocery_service import grocery_service

router = APIRouter(prefix="/optimize", tags=["Multi-Constraint Meal Optimization"])

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Per-meal type calorie targets for explanations
MEAL_EXPLANATIONS = {
    "breakfast": "Provides a balanced start to the day with sustained energy.",
    "pre_workout": "Light, fast-digesting carbs + protein for workout fuel.",
    "post_workout": "High-protein recovery meal to rebuild muscle after training.",
    "lunch": "Largest meal of the day balanced across all macronutrients.",
    "snack": "Low-calorie, high-fiber option to bridge meal gaps.",
    "dinner": "Light, easy-to-digest evening meal to meet remaining daily targets.",
}

def _health_aware_explanation(food, day_name, meal_type, conditions, pathway):
    """Generate a human-readable explanation including health pathway compliance."""
    base = MEAL_EXPLANATIONS.get(meal_type, "Fits your daily nutrition targets.")
    condition_note = ""
    if conditions and "none" not in conditions:
        condition_note = f" Selected within your '{pathway}' dietary profile."
    return f"{base}{condition_note}"


from app.services.profile_service import get_or_create_user_profile

@router.post("/7-day-plan")
def generate_optimized_7day_plan(
    req: OptimizeMealPlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = get_or_create_user_profile(current_user.id, db)

    # Load health profile for disease-aware constraints
    health_prof = db.query(UserHealthProfile).filter(UserHealthProfile.user_id == current_user.id).first()
    health_constraints = {}
    selected_conditions = []
    classified_pathway = "General Wellness Pathway"
    goes_to_gym = False
    if health_prof:
        health_constraints = health_prof.aggregated_constraints or {}
        selected_conditions = health_prof.selected_conditions or []
        classified_pathway = health_prof.classified_pathway or "General Wellness Pathway"
        goes_to_gym = health_prof.goes_to_gym or False

    # Deactivate previous active plans
    db.query(MealPlan).filter(MealPlan.user_id == current_user.id).update({"is_active": False})

    all_foods = db.query(FoodItem).all()

    # Step 1: Safety filter (allergies + dietary preference)
    safe_foods = safety_layer.filter_safe_foods(
        all_foods,
        allergies=profile.allergies,
        dietary_preference=profile.dietary_preference
    )

    # Step 2: Disease-aware food filtering based on health constraints
    if health_constraints:
        max_gi = health_constraints.get("max_glycemic_index", "High")
        max_sat_fat = health_constraints.get("max_saturated_fat_g", 25.0)

        if max_gi == "Medium":
            # For Diabetes/PCOS: remove High-GI foods (white rice items, maida-heavy items)
            high_gi_names = ["white rice", "maida", "fried bread", "puri", "bhatura"]
            safe_foods = [
                f for f in safe_foods
                if not any(h in f.name.lower() for h in high_gi_names)
                   and getattr(f, "glycemic_index", "Medium") != "High"
            ]

        if max_sat_fat <= 15.0:
            # For Cholesterol/Heart: skip deep-fried/high-fat items
            fried_keywords = ["fried", "bhatura", "puri", "samosa"]
            safe_foods = [
                f for f in safe_foods
                if not any(kw in f.name.lower() for kw in fried_keywords)
            ]

    if len(safe_foods) < 8:
        # Safety fallback if too many filtered out
        safe_foods = safety_layer.filter_safe_foods(
            all_foods, allergies=profile.allergies, dietary_preference=profile.dietary_preference
        )

    target_macros = {
        "calories": profile.target_calories or 1750.0,
        "protein_g": profile.target_protein_g or 110.0,
        "carbs_g": profile.target_carbs_g or 190.0,
        "fat_g": profile.target_fat_g or 55.0
    }

    start_dt = datetime.strptime(req.start_date, "%Y-%m-%d") if req.start_date else datetime.utcnow()
    end_dt = start_dt + timedelta(days=6)

    meal_plan = MealPlan(
        user_id=current_user.id,
        is_active=True,
        start_date=start_dt.strftime("%Y-%m-%d"),
        end_date=end_dt.strftime("%Y-%m-%d")
    )
    db.add(meal_plan)
    db.commit()
    db.refresh(meal_plan)

    total_weekly_cost = 0.0
    total_cals_sum = 0.0
    total_pro_sum = 0.0
    created_items = []

    # Organize food pools by category for fast lookup
    foods_by_cat = {}
    for f in safe_foods:
        foods_by_cat.setdefault(f.category, []).append(f)

    # Track used food IDs across the week for strict variety enforcement
    used_food_ids_by_cat = {cat: [] for cat in foods_by_cat}

    for day_idx in range(req.num_days):
        day_name = DAYS_OF_WEEK[day_idx % 7]

        # Build a day-specific candidate pool by strictly excluding recently used foods in each category
        day_candidates = []
        for cat, foods in foods_by_cat.items():
            used_recently = used_food_ids_by_cat.get(cat, [])
            # Dynamic window: exclude foods used in the last (len(foods) - 1) days so no food repeats until pool exhausted
            recent_window = max(1, min(len(used_recently), len(foods) - 1))
            excluded_ids = set(used_recently[-recent_window:]) if recent_window > 0 else set()

            available = [f for f in foods if f.id not in excluded_ids]

            if not available:
                # If pool exhausted, sort by overall usage count ascending + random jitter
                available = sorted(foods, key=lambda f: (used_recently.count(f.id), random.random()))
            else:
                # Shuffle available to provide a unique combination on every regeneration
                random.shuffle(available)

            day_candidates.extend(available)

        if len(day_candidates) < 4:
            day_candidates = safe_foods

        opt_result = diet_optimizer.optimize_daily_meals(
            day_candidates,
            profile,
            target_macros,
            locked_meal_ids=req.locked_meal_item_ids,
            include_workout_meals=goes_to_gym,
            health_constraints=health_constraints
        )

        # Assign meal types properly: breakfast first, then lunch, then dinner, then snack(s)
        selected = opt_result["selected_foods"]

        # Map each selected food to the right meal slot based on its category
        for food in selected:
            used_food_ids_by_cat.setdefault(food.category, []).append(food.id)
            total_weekly_cost += food.approx_cost_inr
            total_cals_sum += food.calories
            total_pro_sum += food.protein_g

            explanation = _health_aware_explanation(
                food, day_name, food.category, selected_conditions, classified_pathway
            )

            plan_item = MealPlanItem(
                meal_plan_id=meal_plan.id,
                day_of_week=day_name,
                meal_type=food.category,
                food_id=food.id,
                food_name=food.name,
                servings=1.0,
                calories=food.calories,
                protein_g=food.protein_g,
                carbs_g=food.carbs_g,
                fat_g=food.fat_g,
                fiber_g=food.fiber_g,
                cost_inr=food.approx_cost_inr,
                recommendation_score=0.92,
                explanation=explanation
            )
            db.add(plan_item)
            created_items.append(plan_item)

    meal_plan.total_weekly_cost_inr = round(total_weekly_cost, 2)
    meal_plan.avg_daily_calories = round(total_cals_sum / req.num_days, 1)
    meal_plan.avg_daily_protein_g = round(total_pro_sum / req.num_days, 1)
    db.commit()

    return {
        "meal_plan_id": meal_plan.id,
        "start_date": meal_plan.start_date,
        "end_date": meal_plan.end_date,
        "health_pathway": classified_pathway,
        "selected_conditions": selected_conditions,
        "summary": {
            "total_weekly_cost_inr": meal_plan.total_weekly_cost_inr,
            "avg_daily_calories": meal_plan.avg_daily_calories,
            "avg_daily_protein_g": meal_plan.avg_daily_protein_g,
            "daily_budget_target_inr": profile.daily_budget_inr
        },
        "days": [
            {
                "day_name": day_name,
                "meals": [
                    {
                        "item_id": item.id,
                        "meal_type": item.meal_type,
                        "food_id": item.food_id,
                        "food_name": item.food_name,
                        "calories": item.calories,
                        "protein_g": item.protein_g,
                        "carbs_g": item.carbs_g,
                        "fat_g": item.fat_g,
                        "cost_inr": item.cost_inr,
                        "is_locked": item.is_locked,
                        "explanation": item.explanation
                    }
                    for item in created_items if item.day_of_week == day_name
                ]
            }
            for day_name in DAYS_OF_WEEK[:req.num_days]
        ]
    }

@router.post("/pantry-meals")
def get_pantry_recipes(
    req: PantryInventoryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    all_foods = db.query(FoodItem).all()

    matches = inventory_engine.find_pantry_recipes(req.available_ingredients, all_foods, profile)
    return {
        "pantry_ingredients_submitted": req.available_ingredients,
        "matched_recipes_count": len(matches),
        "recipes": [
            {
                "food": FoodItemSchema.model_validate(m["food"]),
                "match_pct": m["match_pct"],
                "matched_ingredients": m["matched_ingredients"],
                "missing_ingredients": m["missing_ingredients"],
                "can_cook_immediately": m["can_cook_immediately"]
            }
            for m in matches[:6]
        ]
    }

@router.get("/grocery-list")
def get_active_grocery_list(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan = db.query(MealPlan).filter(MealPlan.user_id == current_user.id, MealPlan.is_active == True).first()
    if not plan:
        req = OptimizeMealPlanRequest()
        generate_optimized_7day_plan(req, current_user, db)
        plan = db.query(MealPlan).filter(MealPlan.user_id == current_user.id, MealPlan.is_active == True).first()

    plan_items = db.query(MealPlanItem).filter(MealPlanItem.meal_plan_id == plan.id).all()
    grocery_data = grocery_service.generate_grocery_list(plan_items)

    return {
        "meal_plan_id": plan.id,
        "start_date": plan.start_date,
        "end_date": plan.end_date,
        "grocery_list": grocery_data
    }
