from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class HealthCondition(Base):
    __tablename__ = "health_conditions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    requires_dynamic_survey = Column(Boolean, default=False)
    category = Column(String, default="chronic")


class ConditionNutritionRule(Base):
    __tablename__ = "condition_nutrition_rules"

    id = Column(Integer, primary_key=True, index=True)
    condition_code = Column(String, index=True, nullable=False)
    rule_key = Column(String, nullable=False)
    constraint_type = Column(String, nullable=False)
    constraint_value = Column(String, nullable=False)
    description = Column(String, nullable=False)


class UserHealthProfile(Base):
    __tablename__ = "user_health_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # Health Condition Selection
    selected_conditions = Column(JSON, default=list)
    not_sure_guidance_requested = Column(Boolean, default=False)

    # Condition-Specific Survey Responses
    condition_details = Column(JSON, default=dict)

    # Workout & Fitness Attributes
    goes_to_gym = Column(Boolean, default=True)
    gym_days_per_week = Column(Integer, default=5)
    daily_steps = Column(Integer, default=6500)
    exercise_frequency = Column(String, default="5 days/week")
    workout_type = Column(String, default="Gym / Strength Training")
    workout_duration_mins = Column(Integer, default=50)
    workout_time = Column(String, default="Evening (6 PM - 8 PM)")

    # Lifestyle Attributes
    sleep_duration_hours = Column(Float, default=7.5)
    wake_up_time = Column(String, default="07:00 AM")
    sleep_time = Column(String, default="11:00 PM")
    work_schedule = Column(String, default="9 AM - 5 PM Desk Job")

    # Classified Pathway & Constraints
    classified_pathway = Column(String, default="General Wellness Pathway")
    aggregated_constraints = Column(JSON, default=dict)
    has_conflicting_conditions = Column(Boolean, default=False)
    clinical_referral_needed = Column(Boolean, default=False)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="health_profile")
