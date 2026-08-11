from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models.food import FoodItem, SubstitutionRule
from app.models.health import HealthCondition
from app.models.user import User, UserProfile
from app.api import auth, profile, recommend, optimize, vision, tracking, assistant, admin, health
from app.seed_data import INDIAN_FOOD_DATASET, DEFAULT_SUBSTITUTION_RULES
from app.services.health_condition_rules import HEALTH_CONDITION_MASTER_DATA

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="NutriTwin – Adaptive AI Nutrition & Health Intelligence Platform API"
)

# Set CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(profile.router, prefix=settings.API_V1_STR)
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(recommend.router, prefix=settings.API_V1_STR)
app.include_router(optimize.router, prefix=settings.API_V1_STR)
app.include_router(vision.router, prefix=settings.API_V1_STR)
app.include_router(tracking.router, prefix=settings.API_V1_STR)
app.include_router(assistant.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)

@app.on_event("startup")
def seed_database_if_empty():
    db = SessionLocal()
    try:
        count = db.query(FoodItem).count()
        if count == 0:
            for item in INDIAN_FOOD_DATASET:
                food = FoodItem(**item)
                db.add(food)
            
            for rule in DEFAULT_SUBSTITUTION_RULES:
                sub = SubstitutionRule(**rule)
                db.add(sub)
                
            db.commit()
            print(f"[NutriTwin Startup] Seeded {len(INDIAN_FOOD_DATASET)} Indian food items into database.")

        cond_count = db.query(HealthCondition).count()
        if cond_count == 0:
            for item in HEALTH_CONDITION_MASTER_DATA:
                cond = HealthCondition(
                    code=item["code"],
                    name=item["name"],
                    category=item["category"],
                    requires_dynamic_survey=item["requires_dynamic_survey"]
                )
                db.add(cond)
            db.commit()
            print(f"[NutriTwin Startup] Seeded {len(HEALTH_CONDITION_MASTER_DATA)} Master Health Conditions.")

    except Exception as e:
        print(f"[NutriTwin Startup Error] {e}")
    finally:
        db.close()

@app.get("/")
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "status": "online",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR
    }
