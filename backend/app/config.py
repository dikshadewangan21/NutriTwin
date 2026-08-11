import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "NutriTwin – Adaptive AI Nutrition Platform"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "nutritwin_super_secret_jwt_key_2026_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    DATABASE_URL: str = "sqlite:///./nutritwin.db"
    
    # ML model storage paths
    MODEL_DIR: str = os.path.join(os.path.dirname(__file__), "..", "ml_artifacts")
    
    class Config:
        case_sensitive = True

settings = Settings()
os.makedirs(settings.MODEL_DIR, exist_ok=True)
