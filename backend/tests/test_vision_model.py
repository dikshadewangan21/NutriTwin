import os
import io
import json
from pathlib import Path
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models.food import FoodItem
from app.ml.vision_classifier import vision_classifier
from app.api.auth import create_access_token

BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = BASE_DIR / "ml_pipeline" / "artifacts"
MODEL_PATH = ARTIFACTS_DIR / "mobilenet_v3_indian_food.pth"
MAPPING_PATH = ARTIFACTS_DIR / "vision_class_mapping.json"
EVAL_PATH = BASE_DIR / "ml_pipeline" / "processed" / "vision_model_evaluation.json"

client = TestClient(app)


def test_vision_model_artifacts_exist():
    """Verify PyTorch model weights, class mapping, and evaluation report exist."""
    assert MODEL_PATH.exists(), f"Model weights file missing at {MODEL_PATH}"
    assert MAPPING_PATH.exists(), f"Class mapping file missing at {MAPPING_PATH}"
    assert EVAL_PATH.exists(), f"Evaluation report file missing at {EVAL_PATH}"


def test_vision_class_mapping_content():
    """Verify class mapping JSON contains 20 Indian food classes."""
    with open(MAPPING_PATH, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    assert "classes" in mapping
    assert len(mapping["classes"]) == 20
    assert "samosa" in mapping["classes"]
    assert "masala_dosa" in mapping["classes"]


def test_vision_classifier_is_loaded():
    """Verify PyTorch MobileNetV3 model is loaded inside vision_classifier instance."""
    assert vision_classifier.is_model_loaded is True
    assert vision_classifier.model is not None


def test_process_image_inference():
    """Test process_image method with a generated sample RGB image."""
    db = SessionLocal()
    try:
        food_items = db.query(FoodItem).all()
        assert len(food_items) > 0

        # Generate sample 224x224 RGB image
        img = Image.new("RGB", (224, 224), color=(200, 100, 50))
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="JPEG")
        img_bytes = img_byte_arr.getvalue()

        result = vision_classifier.process_image(img_bytes, food_items, filename="samosa_sample.jpg")
        
        assert result["success"] is True
        assert "detected_food" in result
        assert "top_candidates" in result
        assert len(result["top_candidates"]) > 0

        detected = result["detected_food"]
        assert detected["calories"] >= 0
        assert detected["protein_g"] >= 0
        assert detected["carbs_g"] >= 0
        assert detected["fat_g"] >= 0
        assert detected["fiber_g"] >= 0
        assert detected["confidence_pct"] > 0
    finally:
        db.close()


def test_scan_meal_api_endpoint():
    """Test /api/v1/vision/scan-meal REST API endpoint with image upload."""
    token = create_access_token(user_id=1, email="test@nutritwin.ai")
    headers = {"Authorization": f"Bearer {token}"}

    # Generate sample 224x224 image bytes
    img = Image.new("RGB", (224, 224), color=(180, 120, 60))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_bytes = img_byte_arr.getvalue()

    files = {"file": ("test_dosa.jpg", img_bytes, "image/jpeg")}

    res = client.post("/api/v1/vision/scan-meal", headers=headers, files=files)
    assert res.status_code == 200, f"Scan meal endpoint failed: {res.text}"

    data = res.json()
    assert data["success"] is True
    assert "detected_food" in data
    assert "top_candidates" in data

    detected = data["detected_food"]
    required_keys = ["food_id", "name", "category", "calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "confidence_pct"]
    for k in required_keys:
        assert k in detected, f"Scan meal response missing key '{k}'"
