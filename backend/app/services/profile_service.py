from sqlalchemy.orm import Session
from app.models.user import UserProfile
from app.services.nutrition_calculator import nutrition_calculator

def get_or_create_user_profile(user_id: int, db: Session) -> UserProfile:
    """
    Retrieves existing UserProfile for given user_id, or automatically constructs,
    seeds, and returns a baseline UserProfile if none exists yet.
    Guarantees downstream ML meal planning and RAG assistant services never fail.
    """
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if profile:
        return profile

    # Compute baseline nutritional requirements for default profile
    nutr = nutrition_calculator.compute_nutritional_profile(
        age=28,
        gender="male",
        height_cm=175.0,
        weight_kg=70.0,
        target_weight_kg=68.0,
        activity_level="moderate",
        fitness_goal="weight_loss"
    )

    profile = UserProfile(
        user_id=user_id,
        age=28,
        gender="male",
        height_cm=175.0,
        current_weight_kg=70.0,
        target_weight_kg=68.0,
        activity_level="moderate",
        fitness_goal="weight_loss",
        dietary_preference="non_vegetarian",
        meals_per_day=4,
        preferred_meal_timings=["08:00", "13:00", "17:00", "20:00"],
        daily_budget_inr=250.0,
        weekly_budget_inr=1750.0,
        location_region="North India",
        allergies=[],
        foods_to_avoid=[],
        medical_conditions=["none"],
        liked_foods=[],
        disliked_foods=[],
        pantry_inventory=[],
        bmr=nutr["bmr"],
        tdee=nutr["tdee"],
        bmi=nutr["bmi"],
        target_calories=nutr["target_calories"],
        target_protein_g=nutr["target_protein_g"],
        target_carbs_g=nutr["target_carbs_g"],
        target_fat_g=nutr["target_fat_g"],
        target_fiber_g=nutr["target_fiber_g"],
        target_hydration_l=nutr["target_hydration_l"],
        assigned_cluster_id=0,
        assigned_cluster_label="Weight-Loss Focused"
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
