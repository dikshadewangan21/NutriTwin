import os
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models.food import FoodItem
from app.schemas.food import FoodItemSchema
from app.api.auth import create_access_token

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "ml_pipeline" / "processed"
CLEANED_JSON = PROCESSED_DIR / "indian_food_cleaned.json"
REPORT_JSON = PROCESSED_DIR / "food_dataset_report.json"

client = TestClient(app)


def test_preprocessing_artifacts_exist():
    """Verify Phase 1 JSON artifacts are present in backend/ml_pipeline/processed/."""
    assert CLEANED_JSON.exists(), f"Cleaned dataset JSON missing at {CLEANED_JSON}"
    assert REPORT_JSON.exists(), f"Statistical report JSON missing at {REPORT_JSON}"


def test_preprocessing_report_counts():
    """Verify statistical report metrics match Phase 1 requirements."""
    with open(REPORT_JSON, "r", encoding="utf-8") as f:
        report = json.load(f)

    assert report["raw_records"] == 255
    assert report["cleaned_records"] == 255
    assert report["invalid_records"] == 0
    assert report["duplicate_records"] == 0
    assert report["matched_records"] + report["unmatched_records"] == 255


def test_cleaned_records_nutrition_integrity():
    """Verify no negative values and fiber <= carbs constraints in cleaned dataset."""
    with open(CLEANED_JSON, "r", encoding="utf-8") as f:
        records = json.load(f)

    for r in records:
        assert r["calories"] >= 0, f"Negative calories in {r['name']}"
        assert r["protein_g"] >= 0, f"Negative protein in {r['name']}"
        assert r["carbs_g"] >= 0, f"Negative carbs in {r['name']}"
        assert r["fat_g"] >= 0, f"Negative fat in {r['name']}"
        assert r["fiber_g"] >= 0, f"Negative fiber in {r['name']}"
        if r["carbs_g"] > 0:
            assert r["fiber_g"] <= r["carbs_g"] + 0.1, f"Fiber exceeds carbs in {r['name']}"


def test_database_food_items_imported():
    """Verify database contains imported Indian Food 101 records."""
    db = SessionLocal()
    try:
        count = db.query(FoodItem).count()
        assert count >= 250, f"Expected at least 250 DB food items, found {count}"

        # Verify all records conform to FoodItemSchema and have no negative macro fields
        items = db.query(FoodItem).all()
        for item in items:
            schema_obj = FoodItemSchema.model_validate(item)
            assert schema_obj.calories >= 0
            assert schema_obj.protein_g >= 0
            assert schema_obj.carbs_g >= 0
            assert schema_obj.fat_g >= 0
            assert schema_obj.fiber_g >= 0
    finally:
        db.close()


def test_api_food_search_contract():
    """Verify API contracts remain unbroken for food search endpoint."""
    token = create_access_token(user_id=1, email="test@nutritwin.ai")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/vision/food-search?q=Paneer&limit=5", headers=headers)
    assert res.status_code == 200, f"Food search endpoint failed: {res.text}"
    data = res.json()
    assert "results" in data
    assert len(data["results"]) > 0

    first_item = data["results"][0]
    required_keys = ["food_id", "name", "category", "calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "confidence_pct"]
    for k in required_keys:
        assert k in first_item, f"API contract missing key '{k}' in food search response"
