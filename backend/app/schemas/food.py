from pydantic import BaseModel
from typing import List, Optional

class FoodItemSchema(BaseModel):
    id: int
    name: str
    name_hindi: Optional[str] = None
    category: str
    cuisine: str
    dietary_type: str
    serving_unit: str
    serving_weight_g: float
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    approx_cost_inr: float
    region: str
    seasonal_months: List[int] = []
    ingredients: List[str] = []
    allergens: List[str] = []
    glycemic_index: Optional[str] = "Medium"
    description: Optional[str] = None

    class Config:
        from_attributes = True

class SubstituteRequest(BaseModel):
    food_id: int

class PantryInventoryRequest(BaseModel):
    available_ingredients: List[str]
