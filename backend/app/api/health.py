from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.database import get_db
from app.models.user import User, UserProfile
from app.models.health import HealthCondition, UserHealthProfile
from app.models.food import FoodItem
from app.api.auth import get_current_user
from app.services.nutrition_calculator import nutrition_calculator
from app.services.health_condition_classifier import health_condition_classifier
from app.services.health_condition_rules import HEALTH_CONDITION_MASTER_DATA, CONDITION_SPECIFIC_SURVEYS
from app.services.safety_layer import safety_layer

router = APIRouter(prefix="/health", tags=["Health Assessment & Disease-Aware Nutrition Engine"])

class HealthAssessmentSubmission(BaseModel):
    selected_conditions: List[str] = []
    not_sure_guidance_requested: bool = False
    condition_details: Dict[str, Any] = {}
    daily_steps: int = 5000
    exercise_frequency: str = "3-4 days/week"
    workout_type: str = "Gym / Strength Training"
    workout_duration_mins: int = 45
    workout_time: str = "Evening (6 PM - 8 PM)"

@router.get("/conditions")
def get_master_health_conditions():
    """Returns master list of health conditions and dynamic survey questions."""
    return {
        "conditions": HEALTH_CONDITION_MASTER_DATA,
        "dynamic_surveys": CONDITION_SPECIFIC_SURVEYS
    }

@router.post("/profile")
def submit_health_assessment(
    data: HealthAssessmentSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submits health assessment survey and classifies user into a Nutrition Pathway."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Please complete basic body profile onboarding first.")

    # Run Disease-Aware Pathway Classifier
    classification = health_condition_classifier.classify_user_pathway(
        selected_conditions=data.selected_conditions,
        workout_type=data.workout_type,
        fitness_goal=profile.fitness_goal
    )

    health_prof = db.query(UserHealthProfile).filter(UserHealthProfile.user_id == current_user.id).first()
    if not health_prof:
        health_prof = UserHealthProfile(user_id=current_user.id)

    health_prof.selected_conditions = data.selected_conditions
    health_prof.not_sure_guidance_requested = data.not_sure_guidance_requested
    health_prof.condition_details = data.condition_details
    health_prof.daily_steps = data.daily_steps
    health_prof.exercise_frequency = data.exercise_frequency
    health_prof.workout_type = data.workout_type
    health_prof.workout_duration_mins = data.workout_duration_mins
    health_prof.workout_time = data.workout_time
    health_prof.classified_pathway = classification["classified_pathway"]
    health_prof.aggregated_constraints = classification["aggregated_constraints"]
    health_prof.has_conflicting_conditions = classification["is_multi_condition"]
    health_prof.clinical_referral_needed = classification["clinical_referral_needed"]

    # Also update profile medical_conditions list
    profile.medical_conditions = data.selected_conditions

    db.add(health_prof)
    db.commit()
    db.refresh(health_prof)

    return {
        "user_id": current_user.id,
        "classified_pathway": health_prof.classified_pathway,
        "selected_conditions": health_prof.selected_conditions,
        "aggregated_constraints": health_prof.aggregated_constraints,
        "clinical_notice": classification["clinical_notice"],
        "workout_schedule": {
            "type": health_prof.workout_type,
            "duration_mins": health_prof.workout_duration_mins,
            "timing": health_prof.workout_time
        }
    }

@router.get("/nutrition-profile")
def get_user_health_nutrition_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetches user health profile, classified pathway, and calculated requirements."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    health_prof = db.query(UserHealthProfile).filter(UserHealthProfile.user_id == current_user.id).first()

    if not profile:
        raise HTTPException(status_code=400, detail="Profile not found.")

    pathway = health_prof.classified_pathway if (health_prof and health_prof.classified_pathway) else "General Health & Wellness Plan"
    conds = health_prof.selected_conditions if (health_prof and health_prof.selected_conditions) else (profile.medical_conditions or [])

    # Format conditions list cleanly
    active_conds = [c for c in conds if c and c.lower() != 'none']

    safety_check = safety_layer.validate_user_safety(profile)

    workout_display = "Moderate Exercise"
    if health_prof and health_prof.workout_type:
        workout_display = health_prof.workout_type
    elif profile.activity_level:
        workout_display = profile.activity_level.replace('_', ' ').title()

    return {
        "user_id": current_user.id,
        "body_summary": {
            "bmi": profile.bmi,
            "bmr": profile.bmr,
            "tdee": profile.tdee,
            "target_calories": profile.target_calories,
            "target_protein_g": profile.target_protein_g,
            "target_carbs_g": profile.target_carbs_g,
            "target_fat_g": profile.target_fat_g,
            "target_fiber_g": profile.target_fiber_g,
            "target_hydration_l": profile.target_hydration_l
        },
        "health_summary": {
            "classified_pathway": pathway,
            "selected_conditions": active_conds if active_conds else ["General Health"],
            "workout_type": workout_display,
            "daily_budget_inr": profile.daily_budget_inr or 250,
            "dietary_preference": profile.dietary_preference or "Flexible",
            "clinical_referral_needed": safety_check["requires_clinical_referral"],
            "safety_warnings": safety_check["safety_warnings"],
            "medical_disclaimer": safety_check["medical_disclaimer"]
        }
    }

@router.post("/recalculate")
def recalculate_user_nutrition(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Recalculates baseline BMR, TDEE, macros, and pathway classification
    whenever weight, target weight, activity, or health condition changes.
    """
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Profile not found.")

    # Re-run nutrition calculation
    nutr = nutrition_calculator.compute_nutritional_profile(
        age=profile.age,
        gender=profile.gender,
        height_cm=profile.height_cm,
        weight_kg=profile.current_weight_kg,
        target_weight_kg=profile.target_weight_kg,
        activity_level=profile.activity_level,
        fitness_goal=profile.fitness_goal
    )

    for field, val in nutr.items():
        setattr(profile, field, val)

    # Re-run classification
    health_prof = db.query(UserHealthProfile).filter(UserHealthProfile.user_id == current_user.id).first()
    if health_prof:
        classification = health_condition_classifier.classify_user_pathway(
            selected_conditions=health_prof.selected_conditions,
            workout_type=health_prof.workout_type,
            fitness_goal=profile.fitness_goal
        )
        health_prof.classified_pathway = classification["classified_pathway"]
        health_prof.aggregated_constraints = classification["aggregated_constraints"]

    db.commit()
    db.refresh(profile)

    return {
        "status": "success",
        "message": "Nutrition requirements and health pathway successfully recalculated.",
        "updated_nutrition": nutr,
        "classified_pathway": health_prof.classified_pathway if health_prof else "General Wellness Pathway"
    }
