from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database import get_db
from app.models.user import User, UserProfile
from app.models.food import FoodItem
from app.models.log import FeedbackLog
from app.schemas.food import FoodItemSchema, SubstituteRequest
from app.schemas.recommend import SingleMealSwapRequest
from app.api.auth import get_current_user
from app.ml.hybrid_recommender import hybrid_recommender
from app.ml.adaptive_engine import adaptive_engine
from app.ml.explainable_ai import explainable_ai
from app.services.safety_layer import safety_layer
from app.services.substitute_engine import substitute_engine

router = APIRouter(prefix="/recommend", tags=["AI Recommendation Engine"])

@router.get("/daily")
def get_daily_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Please complete profile onboarding first.")

    # Fetch safe food candidates
    all_foods = db.query(FoodItem).all()
    safe_foods = safety_layer.filter_safe_foods(
        all_foods,
        allergies=profile.allergies,
        dietary_preference=profile.dietary_preference
    )

    # Fetch user feedback history
    feedback_logs = db.query(FeedbackLog).filter(FeedbackLog.user_id == current_user.id).all()
    f_hist = [
        {"food_id": f.food_id, "action_type": f.action_type, "rating": f.rating}
        for f in feedback_logs
    ]

    target_macros = {
        "calories": profile.target_calories or 2000.0,
        "protein_g": profile.target_protein_g or 75.0,
        "carbs_g": profile.target_carbs_g or 250.0,
        "fat_g": profile.target_fat_g or 65.0
    }

    meal_recommendations = {}
    for slot in ["breakfast", "lunch", "dinner", "snack"]:
        ranked = hybrid_recommender.score_and_rank_foods(
            safe_foods,
            profile,
            target_macros,
            meal_type=slot,
            user_feedback_history=f_hist
        )
        
        # Apply adaptive online learning adjustments
        adapted_ranked = adaptive_engine.update_item_weights(ranked, f_hist)
        
        # Format top 3 options per slot
        meal_recommendations[slot] = [
            {
                "food": FoodItemSchema.model_validate(item["food"]),
                "recommendation_score": item["score"],
                "score_breakdown": item["breakdown"],
                "explanation": explainable_ai.explain_recommendation(
                    item["food"], item, profile, target_macros
                )
            }
            for item in adapted_ranked[:3]
        ]

    return {
        "user_id": current_user.id,
        "daily_target_calories": profile.target_calories,
        "recommendations_by_meal": meal_recommendations
    }

@router.post("/substitute")
def get_smart_substitute(
    req: SubstituteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_food = db.query(FoodItem).filter(FoodItem.id == req.food_id).first()
    if not target_food:
        raise HTTPException(status_code=404, detail="Food item not found.")

    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    all_foods = db.query(FoodItem).all()

    substitutes = substitute_engine.find_substitutes(target_food, all_foods, profile)
    
    return {
        "original_food": FoodItemSchema.model_validate(target_food),
        "recommended_substitutes": [
            {
                "substitute_food": FoodItemSchema.model_validate(s["substitute_food"]),
                "match_score_pct": s["match_score_pct"],
                "reason": s["reason"],
                "macro_diff": s["macro_diff"]
            }
            for s in substitutes
        ]
    }

@router.get("/explain/{food_id}")
def explain_food_recommendation(
    food_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    food = db.query(FoodItem).filter(FoodItem.id == food_id).first()
    if not food:
        raise HTTPException(status_code=404, detail="Food item not found.")

    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    target_macros = {
        "calories": profile.target_calories or 2000.0,
        "protein_g": profile.target_protein_g or 75.0,
        "carbs_g": profile.target_carbs_g or 250.0,
        "fat_g": profile.target_fat_g or 65.0
    }

    mock_score_item = {
        "score": 0.88,
        "breakdown": {"macro_fit": 0.9, "preference_fit": 0.85, "budget_fit": 0.95, "diversity_score": 1.0, "region_boost": 1.0}
    }
    
    explanation = explainable_ai.explain_recommendation(food, mock_score_item, profile, target_macros)
    return explanation
