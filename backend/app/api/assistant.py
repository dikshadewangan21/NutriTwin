from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User, UserProfile
from app.models.food import FoodItem
from app.models.log import DailyIntakeLog
from app.api.auth import get_current_user
from app.services.rag_assistant import rag_assistant

router = APIRouter(prefix="/assistant", tags=["Grounded RAG AI Nutrition Assistant"])

class ChatRequest(BaseModel):
    query: str

@router.post("/chat")
def chat_with_nutrition_assistant(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Please complete profile onboarding first.")

    today_str = "2026-08-08"
    intake = db.query(DailyIntakeLog).filter(
        DailyIntakeLog.user_id == current_user.id,
        DailyIntakeLog.log_date == today_str
    ).first()

    all_foods = db.query(FoodItem).all()

    res = rag_assistant.process_chat_query(req.query, profile, intake, all_foods)
    return res
