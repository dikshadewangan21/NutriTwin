import os
import json
from pathlib import Path
import pytest
import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.food import FoodItem
from app.models.log import RecommendationInteraction
from app.api.auth import create_access_token, get_current_user
from ml_pipeline.export_interactions import export_user_meal_interactions, CSV_OUT_PATH, REPORT_OUT_PATH

Base.metadata.create_all(bind=engine)

def get_test_user():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "test_interaction@nutritwin.ai").first()
        if not user:
            user = User(email="test_interaction@nutritwin.ai", hashed_password="pw", full_name="Test Interaction User")
            db.add(user)
            db.commit()
            db.refresh(user)
        return user.id, user.email
    finally:
        db.close()

def mock_get_current_user():
    uid, email = get_test_user()
    db = SessionLocal()
    try:
        return db.query(User).filter(User.id == uid).first()
    finally:
        db.close()

app.dependency_overrides[get_current_user] = mock_get_current_user
client = TestClient(app)


def test_create_and_log_database_interaction():
    """Verify RecommendationInteraction model logs correctly into database."""
    db = SessionLocal()
    try:
        uid, email = get_test_user()
        food = db.query(FoodItem).first()
        food_id = food.id if food else 1

        interaction = RecommendationInteraction(
            user_id=uid,
            food_id=food_id,
            shown=True,
            clicked=True,
            consumed=True,
            skipped=False,
            swapped=False,
            rating=4.5,
            context={"meal_type": "lunch", "source": "test"}
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)

        fetched = db.query(RecommendationInteraction).filter(RecommendationInteraction.id == interaction.id).first()
        assert fetched is not None
        assert fetched.user_id == uid
        assert fetched.food_id == food_id
        assert fetched.shown is True
        assert fetched.clicked is True
        assert fetched.consumed is True
        assert fetched.rating == 4.5
        assert fetched.context.get("meal_type") == "lunch"
    finally:
        db.close()


def test_post_interaction_api_endpoint():
    """Test POST /api/v1/recommend/interaction REST API endpoint."""
    uid, email = get_test_user()
    token = create_access_token(user_id=uid, email=email)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "food_id": 1,
        "shown": True,
        "clicked": True,
        "consumed": True,
        "skipped": False,
        "swapped": False,
        "rating": 5.0,
        "context": {"meal_type": "dinner", "device": "web"}
    }

    res = client.post("/api/v1/recommend/interaction", headers=headers, json=payload)
    assert res.status_code == 200, f"Interaction endpoint failed: {res.text}"
    
    data = res.json()
    assert "interaction_id" in data
    assert data["user_id"] > 0
    assert data["food_id"] == 1
    assert data["shown"] is True
    assert data["clicked"] is True
    assert data["consumed"] is True
    assert data["rating"] == 5.0


def test_export_interactions_pipeline():
    """Verify export_interactions pipeline exports database records to CSV."""
    df = export_user_meal_interactions()

    assert CSV_OUT_PATH.exists(), f"Output CSV missing at {CSV_OUT_PATH}"
    assert REPORT_OUT_PATH.exists(), f"Output report missing at {REPORT_OUT_PATH}"
    
    assert "interaction_id" in df.columns
    assert "user_id" in df.columns
    assert "food_id" in df.columns
    assert "shown" in df.columns
    assert "clicked" in df.columns
    assert "consumed" in df.columns
    assert "skipped" in df.columns
    assert "swapped" in df.columns
    assert "rating" in df.columns
    assert "context_json" in df.columns

    assert len(df) >= 2
