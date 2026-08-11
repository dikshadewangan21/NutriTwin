from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class DailyIntakeLog(Base):
    __tablename__ = "daily_intake_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    log_date = Column(String, index=True, nullable=False) # 'YYYY-MM-DD'
    
    total_calories = Column(Float, default=0.0)
    total_protein_g = Column(Float, default=0.0)
    total_carbs_g = Column(Float, default=0.0)
    total_fat_g = Column(Float, default=0.0)
    total_fiber_g = Column(Float, default=0.0)
    water_ml = Column(Float, default=0.0)
    
    logged_items = Column(JSON, default=list) # List of logged meal dictionaries

    user = relationship("User", back_populates="intake_logs")


class MealPlan(Base):
    __tablename__ = "meal_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    start_date = Column(String, nullable=False)
    end_date = Column(String, nullable=False)
    
    total_weekly_cost_inr = Column(Float, default=0.0)
    avg_daily_calories = Column(Float, default=0.0)
    avg_daily_protein_g = Column(Float, default=0.0)
    
    items = relationship("MealPlanItem", back_populates="meal_plan", cascade="all, delete-orphan")
    user = relationship("User", back_populates="meal_plans")


class MealPlanItem(Base):
    __tablename__ = "meal_plan_items"

    id = Column(Integer, primary_key=True, index=True)
    meal_plan_id = Column(Integer, ForeignKey("meal_plans.id"), nullable=False)
    day_of_week = Column(String, nullable=False) # 'Monday', 'Tuesday'...
    meal_type = Column(String, nullable=False)   # 'breakfast', 'snack_1', 'lunch', 'snack_2', 'dinner'
    
    food_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)
    food_name = Column(String, nullable=False)
    servings = Column(Float, default=1.0)
    
    calories = Column(Float, nullable=False)
    protein_g = Column(Float, nullable=False)
    carbs_g = Column(Float, nullable=False)
    fat_g = Column(Float, nullable=False)
    fiber_g = Column(Float, default=2.0)
    cost_inr = Column(Float, nullable=False)
    
    is_locked = Column(Boolean, default=False)
    is_consumed = Column(Boolean, default=False)
    is_skipped = Column(Boolean, default=False)
    
    recommendation_score = Column(Float, default=0.0)
    explanation = Column(Text, nullable=True)

    meal_plan = relationship("MealPlan", back_populates="items")


class FeedbackLog(Base):
    __tablename__ = "feedback_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    food_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)
    meal_plan_item_id = Column(Integer, nullable=True)
    
    action_type = Column(String, nullable=False) # 'consumed', 'skipped', 'swapped', 'rated'
    rating = Column(Float, nullable=True)
    reason = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="feedback_logs")


class ModelMetric(Base):
    __tablename__ = "model_metrics"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, nullable=False) # 'KMeansClustering', 'HybridRecommender', 'ProgressPredictor'
    metric_name = Column(String, nullable=False) # 'precision_at_k', 'ndcg_at_k', 'silhouette_score', 'mae', 'r2'
    metric_value = Column(Float, nullable=False)
    details = Column(JSON, default=dict)
    evaluated_at = Column(DateTime, default=datetime.utcnow)
