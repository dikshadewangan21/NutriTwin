from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    full_name: str
    email: str

class UserProfileCreate(BaseModel):
    age: int
    gender: str
    height_cm: float
    current_weight_kg: float
    target_weight_kg: float
    activity_level: str
    fitness_goal: str
    dietary_preference: str
    daily_budget_inr: float = 300.0
    weekly_budget_inr: float = 2100.0
    location_region: str = "North India"
    allergies: List[str] = []
    medical_conditions: List[str] = []
    liked_foods: List[str] = []
    disliked_foods: List[str] = []
    pantry_inventory: List[str] = []

class UserProfileResponse(BaseModel):
    id: int
    user_id: int
    age: int
    gender: str
    height_cm: float
    current_weight_kg: float
    target_weight_kg: float
    activity_level: str
    fitness_goal: str
    dietary_preference: str
    daily_budget_inr: float
    weekly_budget_inr: float
    location_region: str
    allergies: List[str]
    medical_conditions: List[str]
    liked_foods: List[str]
    disliked_foods: List[str]
    pantry_inventory: List[str]
    bmr: Optional[float] = None
    tdee: Optional[float] = None
    bmi: Optional[float] = None
    target_calories: Optional[float] = None
    target_protein_g: Optional[float] = None
    target_carbs_g: Optional[float] = None
    target_fat_g: Optional[float] = None
    target_fiber_g: Optional[float] = None
    target_hydration_l: Optional[float] = None
    assigned_cluster_id: Optional[int] = None
    assigned_cluster_label: Optional[str] = None

    class Config:
        from_attributes = True
