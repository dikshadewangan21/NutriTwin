import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "NutriTwin – Adaptive AI Nutrition Platform"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("NUTRITWIN_JWT_SECRET", os.getenv("SECRET_KEY", "nutritwin_super_secret_jwt_key_2026_production"))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    ALLOWED_CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://nutritwin.ai"
    ]

    DATABASE_URL: str = "sqlite:///./nutritwin.db"
    
    # ML model storage paths
    MODEL_DIR: str = os.path.join(os.path.dirname(__file__), "..", "ml_artifacts")
    
    class Config:
        case_sensitive = True

settings = Settings()
os.makedirs(settings.MODEL_DIR, exist_ok=True)
