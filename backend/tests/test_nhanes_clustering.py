import os
import json
from pathlib import Path
import pytest
import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models.user import User
from app.ml.clustering import clustering_model
from app.api.auth import create_access_token, get_current_user

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "ml_pipeline" / "processed"
ARTIFACTS_DIR = BASE_DIR / "ml_pipeline" / "artifacts"

CLEANED_CSV = PROCESSED_DIR / "nhanes_user_profiles_cleaned.csv"
REPORT_JSON = PROCESSED_DIR / "clustering_evaluation_report.json"
MODEL_PATH = ARTIFACTS_DIR / "kmeans_user_cluster.joblib"
SCALER_PATH = ARTIFACTS_DIR / "scaler_user_cluster.joblib"
METADATA_PATH = ARTIFACTS_DIR / "cluster_metadata.json"

def mock_get_current_user():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "test_cluster@nutritwin.ai").first()
        if not user:
            user = User(email="test_cluster@nutritwin.ai", hashed_password="pw", full_name="Test Cluster User")
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    finally:
        db.close()

app.dependency_overrides[get_current_user] = mock_get_current_user
client = TestClient(app)


def test_nhanes_artifacts_exist():
    """Verify NHANES processed CSV, metadata JSON, and joblib artifacts exist."""
    assert CLEANED_CSV.exists(), f"Cleaned NHANES CSV missing at {CLEANED_CSV}"
    assert REPORT_JSON.exists(), f"Evaluation report JSON missing at {REPORT_JSON}"
    assert MODEL_PATH.exists(), f"KMeans model artifact missing at {MODEL_PATH}"
    assert SCALER_PATH.exists(), f"Scaler artifact missing at {SCALER_PATH}"
    assert METADATA_PATH.exists(), f"Metadata JSON missing at {METADATA_PATH}"


def test_nhanes_cleaned_csv_integrity():
    """Verify cleaned NHANES CSV contains adult user profiles without missing values."""
    df = pd.read_csv(CLEANED_CSV)
    assert len(df) >= 4000, f"Expected >= 4000 valid NHANES adult profiles, found {len(df)}"

    required_cols = ["age", "bmi", "weight_kg", "height_cm", "daily_calories", "protein_g", "carbs_g", "fat_g", "activity_score"]
    for col in required_cols:
        assert col in df.columns, f"Cleaned CSV missing column '{col}'"
        assert df[col].isnull().sum() == 0, f"Cleaned CSV column '{col}' contains NaN values"
        assert (df[col] >= 0).all(), f"Cleaned CSV column '{col}' contains negative values"


def test_kmeans_metadata_dynamic_metrics():
    """Verify cluster_metadata.json contains dynamic empirical metrics from real NHANES training."""
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["num_clusters"] == 6
    assert meta["sample_count"] >= 4000

    metrics = meta["metrics"]
    assert "silhouette_score" in metrics
    assert "davies_bouldin_index" in metrics
    assert "inertia" in metrics

    assert metrics["silhouette_score"] > 0.10
    assert metrics["davies_bouldin_index"] > 0.50
    assert metrics["inertia"] > 1000.0


def test_clustering_model_predict_persona():
    """Test user persona prediction using real-data trained K-Means model."""
    sample_profile = {
        "age": 28,
        "bmi": 24.2,
        "target_calories": 2200.0,
        "target_protein_g": 90.0,
        "daily_budget_inr": 350.0,
        "activity_level": "very_active",
        "fitness_goal": "muscle_gain",
        "dietary_preference": "non_vegetarian"
    }

    result = clustering_model.predict_cluster(sample_profile)
    assert "cluster_id" in result
    assert 0 <= result["cluster_id"] < 6
    assert "label" in result
    assert "description" in result
    assert "key_traits" in result
    assert len(result["key_traits"]) > 0


def test_profile_onboarding_api_contract():
    """Verify profile onboarding endpoint works and predicts user persona."""
    token = create_access_token(user_id=1, email="test_cluster@nutritwin.ai")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "age": 26,
        "gender": "male",
        "height_cm": 178.0,
        "current_weight_kg": 74.0,
        "target_weight_kg": 78.0,
        "activity_level": "moderate",
        "fitness_goal": "muscle_gain",
        "dietary_preference": "vegetarian",
        "daily_budget_inr": 300.0,
        "allergies": [],
        "health_conditions": []
    }

    res = client.post("/api/v1/profile/onboard", headers=headers, json=payload)
    assert res.status_code == 200, f"Profile onboarding failed: {res.text}"
    data = res.json()
    assert "user_id" in data
    assert "assigned_cluster_id" in data
    assert "assigned_cluster_label" in data
    assert 0 <= data["assigned_cluster_id"] < 6
