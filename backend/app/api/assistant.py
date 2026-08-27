from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date

from app.database import get_db
from app.models.user import User, UserProfile
from app.models.food import FoodItem, SubstitutionRule
from app.models.log import DailyIntakeLog
from app.api.auth import get_current_user
from app.services.rag_assistant import rag_assistant

router = APIRouter(prefix="/assistant", tags=["Grounded RAG AI Nutrition Assistant"])

class ChatRequest(BaseModel):
    query: str
    history: Optional[List[Dict[str, Any]]] = []

from app.services.profile_service import get_or_create_user_profile

@router.post("/chat")
def chat_with_nutrition_assistant(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = get_or_create_user_profile(current_user.id, db)

    today_str = date.today().isoformat()
    intake = db.query(DailyIntakeLog).filter(
        DailyIntakeLog.user_id == current_user.id,
        DailyIntakeLog.log_date == today_str
    ).first()

    all_foods = db.query(FoodItem).all()
    sub_rules = db.query(SubstitutionRule).all()

    res = rag_assistant.process_chat_query(
        user_query=req.query,
        user_profile=profile,
        daily_intake=intake,
        food_items=all_foods,
        substitution_rules=sub_rules,
        chat_history=req.history
    )
    return res
