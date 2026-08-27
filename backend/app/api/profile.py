from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserProfile
from app.schemas.user import UserProfileCreate, UserProfileResponse
from app.api.auth import get_current_user
from app.services.nutrition_calculator import nutrition_calculator
from app.services.safety_layer import safety_layer
from app.ml.clustering import clustering_model

router = APIRouter(prefix="/profile", tags=["User Profile & Onboarding"])

@router.post("/onboard", response_model=UserProfileResponse)
def create_or_update_profile(
    profile_in: UserProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Compute Base Nutrition Requirements
    nutr = nutrition_calculator.compute_nutritional_profile(
        age=profile_in.age,
        gender=profile_in.gender,
        height_cm=profile_in.height_cm,
        weight_kg=profile_in.current_weight_kg,
        target_weight_kg=profile_in.target_weight_kg,
        activity_level=profile_in.activity_level,
        fitness_goal=profile_in.fitness_goal
    )

    # 2. Run K-Means Clustering for ML User Profiling
    profile_dict_for_ml = profile_in.model_dump()
    profile_dict_for_ml.update(nutr)
    cluster_res = clustering_model.predict_cluster(profile_dict_for_ml)

    # 3. Check database for existing profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)

    # Populate fields
    for field, val in profile_in.model_dump().items():
        setattr(profile, field, val)

    profile.bmr = nutr["bmr"]
    profile.tdee = nutr["tdee"]
    profile.bmi = nutr["bmi"]
    profile.target_calories = nutr["target_calories"]
    profile.target_protein_g = nutr["target_protein_g"]
    profile.target_carbs_g = nutr["target_carbs_g"]
    profile.target_fat_g = nutr["target_fat_g"]
    profile.target_fiber_g = nutr["target_fiber_g"]
    profile.target_hydration_l = nutr["target_hydration_l"]

    profile.assigned_cluster_id = cluster_res["cluster_id"]
    profile.assigned_cluster_label = cluster_res["label"]

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile

from app.services.profile_service import get_or_create_user_profile

@router.get("/me", response_model=UserProfileResponse)
def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = get_or_create_user_profile(current_user.id, db)
    return profile

@router.get("/cluster-info")
def get_cluster_details(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile or profile.assigned_cluster_id is None:
        return {"assigned": False, "cluster_info": None}

    prof_dict = {
        "age": profile.age,
        "bmi": profile.bmi,
        "target_calories": profile.target_calories,
        "target_protein_g": profile.target_protein_g,
        "daily_budget_inr": profile.daily_budget_inr,
        "activity_level": profile.activity_level,
        "fitness_goal": profile.fitness_goal,
        "dietary_preference": profile.dietary_preference
    }
    cluster_res = clustering_model.predict_cluster(prof_dict)
    safety_check = safety_layer.validate_user_safety(profile)

    return {
        "assigned": True,
        "user_id": current_user.id,
        "cluster": cluster_res,
        "safety_audit": safety_check
    }
