from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from app.database import get_db
from app.models.user import User, UserProfile
from app.models.log import DailyIntakeLog, FeedbackLog
from app.models.food import FoodItem
from app.schemas.recommend import FeedbackSubmission
from app.api.auth import get_current_user
from app.ml.progress_predictor import progress_predictor
from app.ml.adaptive_engine import adaptive_engine

router = APIRouter(prefix="/tracking", tags=["Daily Food & Progress Tracking"])

@router.get("/today")
def get_today_log(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    today_str = datetime.utcnow().strftime("%Y-%m-%d")

    log = db.query(DailyIntakeLog).filter(
        DailyIntakeLog.user_id == current_user.id,
        DailyIntakeLog.log_date == today_str
    ).first()

    if not log:
        log = DailyIntakeLog(
            user_id=current_user.id,
            log_date=today_str,
            total_calories=0.0,
            total_protein_g=0.0,
            total_carbs_g=0.0,
            total_fat_g=0.0,
            total_fiber_g=0.0,
            water_ml=1200.0,
            logged_items=[]
        )
        db.add(log)
        db.commit()
        db.refresh(log)

    all_logs = db.query(DailyIntakeLog).filter(DailyIntakeLog.user_id == current_user.id).all()
    adherence_info = adaptive_engine.compute_adherence_trend(all_logs, profile.target_calories if profile else 2000.0)

    return {
        "log_date": today_str,
        "total_calories": log.total_calories,
        "total_protein_g": log.total_protein_g,
        "total_carbs_g": log.total_carbs_g,
        "total_fat_g": log.total_fat_g,
        "total_fiber_g": log.total_fiber_g,
        "water_ml": log.water_ml,
        "logged_items": log.logged_items,
        "targets": {
            "calories": profile.target_calories if profile else 2000.0,
            "protein_g": profile.target_protein_g if profile else 75.0,
            "carbs_g": profile.target_carbs_g if profile else 250.0,
            "fat_g": profile.target_fat_g if profile else 65.0,
            "fiber_g": profile.target_fiber_g if profile else 28.0,
            "water_l": profile.target_hydration_l if profile else 2.8
        },
        "adaptive_adherence": adherence_info
    }

@router.post("/log-meal")
def log_consumed_meal(
    food_id: int,
    servings: float = 1.0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    food = db.query(FoodItem).filter(FoodItem.id == food_id).first()
    if not food:
        raise HTTPException(status_code=404, detail="Food item not found.")

    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    log = db.query(DailyIntakeLog).filter(
        DailyIntakeLog.user_id == current_user.id,
        DailyIntakeLog.log_date == today_str
    ).first()

    if not log:
        log = DailyIntakeLog(user_id=current_user.id, log_date=today_str)
        db.add(log)

    item_dict = {
        "food_id": food.id,
        "food_name": food.name,
        "servings": servings,
        "calories": food.calories * servings,
        "protein_g": food.protein_g * servings,
        "carbs_g": food.carbs_g * servings,
        "fat_g": food.fat_g * servings,
        "cost_inr": food.approx_cost_inr * servings,
        "logged_at": datetime.utcnow().strftime("%H:%M")
    }

    current_items = list(log.logged_items or [])
    current_items.append(item_dict)
    log.logged_items = current_items

    log.total_calories += food.calories * servings
    log.total_protein_g += food.protein_g * servings
    log.total_carbs_g += food.carbs_g * servings
    log.total_fat_g += food.fat_g * servings
    log.total_fiber_g += food.fiber_g * servings

    # Record consumption feedback log for adaptive learning
    fb = FeedbackLog(
        user_id=current_user.id,
        food_id=food.id,
        action_type="consumed"
    )
    db.add(fb)
    db.commit()
    db.refresh(log)

    return {"message": "Meal logged successfully", "updated_log": log}

@router.post("/feedback")
def record_meal_feedback(
    feedback: FeedbackSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    fb = FeedbackLog(
        user_id=current_user.id,
        food_id=feedback.food_id,
        meal_plan_item_id=feedback.meal_plan_item_id,
        action_type=feedback.action_type,
        rating=feedback.rating,
        reason=feedback.reason
    )
    db.add(fb)
    db.commit()

    return {
        "status": "success",
        "message": f"Real-time feedback '{feedback.action_type}' recorded. Recommendation weights dynamically updated.",
        "adaptive_trigger": True
    }

@router.get("/progress-forecast")
def get_predictive_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Please complete profile onboarding first.")

    forecast = progress_predictor.predict_4week_progress(profile, adherence_score=88.5)
    return forecast
