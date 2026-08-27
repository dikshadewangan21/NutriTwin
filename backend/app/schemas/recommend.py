from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.schemas.food import FoodItemSchema

class SingleMealSwapRequest(BaseModel):
    meal_plan_item_id: int
    user_dislikes_current: bool = False

class OptimizeMealPlanRequest(BaseModel):
    start_date: str = "2026-08-10"
    num_days: int = 7
    locked_meal_item_ids: List[int] = []

class FeedbackSubmission(BaseModel):
    food_id: int
    action_type: str # 'consumed', 'skipped', 'swapped', 'rated'
    rating: Optional[float] = None
    reason: Optional[str] = None
    meal_plan_item_id: Optional[int] = None


class InteractionLogRequest(BaseModel):
    food_id: int
    shown: bool = True
    clicked: bool = False
    consumed: bool = False
    skipped: bool = False
    swapped: bool = False
    rating: Optional[float] = None
    context: Dict[str, Any] = {}


class InteractionLogResponse(BaseModel):
    interaction_id: int
    user_id: int
    food_id: int
    timestamp: str
    shown: bool
    clicked: bool
    consumed: bool
    skipped: bool
    swapped: bool
    rating: Optional[float] = None
    context: Dict[str, Any] = {}

