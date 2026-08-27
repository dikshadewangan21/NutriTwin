from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    health_profile = relationship("UserHealthProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    intake_logs = relationship("DailyIntakeLog", back_populates="user", cascade="all, delete-orphan")
    meal_plans = relationship("MealPlan", back_populates="user", cascade="all, delete-orphan")
    feedback_logs = relationship("FeedbackLog", back_populates="user", cascade="all, delete-orphan")
    recommendation_interactions = relationship("RecommendationInteraction", back_populates="user", cascade="all, delete-orphan")



class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Physical attributes
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)  # 'male', 'female', 'other'
    height_cm = Column(Float, nullable=False)
    current_weight_kg = Column(Float, nullable=False)
    target_weight_kg = Column(Float, nullable=False)
    
    # Lifestyle & Goals
    activity_level = Column(String, nullable=False)  # 'sedentary', 'light', 'moderate', 'very_active', 'extra_active'
    fitness_goal = Column(String, nullable=False)   # 'weight_loss', 'muscle_gain', 'maintenance', 'health'
    dietary_preference = Column(String, nullable=False) # 'vegetarian', 'vegan', 'eggetarian', 'non_vegetarian', 'jain'
    meals_per_day = Column(Integer, default=4)
    preferred_meal_timings = Column(JSON, default=list)
    
    # Financial & Location
    daily_budget_inr = Column(Float, default=250.0)
    weekly_budget_inr = Column(Float, default=1750.0)
    location_region = Column(String, default="North India")
    
    # Restrictions & Likes (Stored as JSON lists)
    allergies = Column(JSON, default=list)
    foods_to_avoid = Column(JSON, default=list)
    medical_conditions = Column(JSON, default=list)
    liked_foods = Column(JSON, default=list)
    disliked_foods = Column(JSON, default=list)
    pantry_inventory = Column(JSON, default=list)
    
    # Calculated Base Requirements
    bmr = Column(Float, nullable=True)
    tdee = Column(Float, nullable=True)
    bmi = Column(Float, nullable=True)
    target_calories = Column(Float, nullable=True)
    target_protein_g = Column(Float, nullable=True)
    target_carbs_g = Column(Float, nullable=True)
    target_fat_g = Column(Float, nullable=True)
    target_fiber_g = Column(Float, nullable=True)
    target_hydration_l = Column(Float, nullable=True)
    
    # ML Cluster Tag
    assigned_cluster_id = Column(Integer, nullable=True)
    assigned_cluster_label = Column(String, nullable=True)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")
