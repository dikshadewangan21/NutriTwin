from sqlalchemy import Column, Integer, String, Float, Boolean, Text, JSON
from app.database import Base

class FoodItem(Base):
    __tablename__ = "food_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    name_hindi = Column(String, nullable=True)
    category = Column(String, index=True, nullable=False) # 'breakfast', 'lunch', 'dinner', 'snack'
    cuisine = Column(String, default="North Indian")       # 'North Indian', 'South Indian', 'Pan-Indian', etc.
    dietary_type = Column(String, nullable=False)         # 'vegetarian', 'vegan', 'eggetarian', 'non_vegetarian'
    
    # Serving & Macros
    serving_unit = Column(String, nullable=False)        # '1 bowl', '2 pieces', '1 plate'
    serving_weight_g = Column(Float, default=150.0)
    calories = Column(Float, nullable=False)
    protein_g = Column(Float, nullable=False)
    carbs_g = Column(Float, nullable=False)
    fat_g = Column(Float, nullable=False)
    fiber_g = Column(Float, default=2.0)
    
    # Cost & Region
    approx_cost_inr = Column(Float, nullable=False)      # Cost per serving in INR
    region = Column(String, default="All India")
    seasonal_months = Column(JSON, default=list)         # List of months [1, 2, 3...] when seasonal/fresh
    
    # Ingredients & Allergens
    ingredients = Column(JSON, default=list)             # ['paneer', 'spinach', 'spices']
    allergens = Column(JSON, default=list)               # ['lactose', 'gluten', 'peanuts']
    
    # Metadata
    image_url = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    glycemic_index = Column(String, default="Medium")    # 'Low', 'Medium', 'High'
    preparation_time_mins = Column(Integer, default=20)


class SubstitutionRule(Base):
    __tablename__ = "substitution_rules"

    id = Column(Integer, primary_key=True, index=True)
    original_food_name = Column(String, nullable=False, index=True)
    substitute_food_name = Column(String, nullable=False)
    substitute_category = Column(String, nullable=False)
    nutritional_match_score = Column(Float, default=0.9)
    reason = Column(String, nullable=False)
