import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models.food import FoodItem
from app.ml.vision_classifier import vision_classifier
from app.services.rag_assistant import rag_assistant
from app.ml.hybrid_recommender import hybrid_recommender
from app.api.auth import create_access_token
from app.schemas.recommend import OptimizeMealPlanRequest

client = TestClient(app)

class DummyUserProfile:
    full_name = "Test User"
    fitness_goal = "weight_loss"
    dietary_preference = "vegetarian"
    daily_budget_inr = 100.0
    medical_conditions = ["none"]
    target_calories = 1800.0
    target_protein_g = 80.0
    target_carbs_g = 220.0
    target_fat_g = 50.0
    location_region = "North India"
    allergies = []
    liked_foods = []
    disliked_foods = []

class DummyFoodItem:
    def __init__(self, fid, name, cal, pro, carbs, fat, cost, cat, pref="vegetarian"):
        self.id = fid
        self.name = name
        self.serving_unit = "1 bowl"
        self.serving_weight_g = 150.0
        self.calories = cal
        self.protein_g = pro
        self.carbs_g = carbs
        self.fat_g = fat
        self.fiber_g = 3.0
        self.approx_cost_inr = cost
        self.category = cat
        self.dietary_type = pref
        self.region = "All India"
        self.allergens = []
        self.glycemic_index = "Medium"
        self.ingredients = [name.lower()]
        self.description = f"Fresh {name}"


def test_food_scanner_ux_fix():
    """Verify Issue 1 Fix: Class mapping, low confidence handling, and calorie disclaimers."""
    # 1. Class mapping check
    assert vision_classifier._format_class_name("chole_bhature") == "Chole Bhature"
    assert vision_classifier._format_class_name("burger") == "Veg Burger"

    # 2. Low confidence image check (gray canvas)
    img = Image.new("RGB", (224, 224), color=(120, 120, 120))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_bytes = img_byte_arr.getvalue()

    db = SessionLocal()
    try:
        food_items = db.query(FoodItem).all()
        res = vision_classifier.process_image(img_bytes, food_items, filename="gray.jpg")
        
        assert res["success"] is True
        assert "is_confident" in res
        assert "disclaimer" in res
        assert "estimated" in res["disclaimer"].lower() or "database" in res["disclaimer"].lower()
    finally:
        db.close()


def test_rag_assistant_ux_fix():
    """Verify Issue 2 Fix: 'I have ₹100 budget give me full day plan' generates human-friendly structured plan."""
    profile = DummyUserProfile()
    food_list = [
        DummyFoodItem(1, "Poha with Peanuts & Veggies", 270, 6.5, 45, 7.5, 20.0, "breakfast"),
        DummyFoodItem(2, "Dal Tadka with 2 Rotis", 410, 14.0, 62, 10.0, 35.0, "lunch"),
        DummyFoodItem(3, "Masala Chai & Biscuits", 90, 2.0, 15, 2.5, 10.0, "snack"),
        DummyFoodItem(4, "Khichdi with Ghee", 320, 9.5, 52, 7.0, 30.0, "dinner")
    ]

    res = rag_assistant.process_chat_query("I have ₹100 budget give me full day plan", profile, None, food_list)
    assert res is not None
    assert "response" in res
    
    resp_text = res["response"]
    assert "Breakfast" in resp_text or "🍳" in resp_text
    assert "Lunch" in resp_text or "🍛" in resp_text
    assert "Dinner" in resp_text or "🍲" in resp_text
    assert "Total" in resp_text or "Budget" in resp_text
    # Verify no technical jargon in user response
    assert "FAISS" not in resp_text
    assert "chunk_id" not in resp_text


def test_recommendations_meal_type_ux_fix():
    """Verify Issue 3 Fix: meal_type is used so Breakfast gets breakfast foods, Lunch gets lunch foods, Dinner gets dinner foods."""
    profile = DummyUserProfile()
    target_macros = {"calories": 2000.0, "protein_g": 75.0, "carbs_g": 250.0, "fat_g": 65.0}

    food_list = [
        DummyFoodItem(1, "Poha with Peanuts & Veggies", 270, 6.5, 45, 7.5, 20.0, "breakfast"),
        DummyFoodItem(2, "Dal Makhani with Naan", 550, 16.0, 75, 18.0, 120.0, "dinner"),
        DummyFoodItem(3, "Roasted Chana", 150, 8.0, 22, 3.0, 15.0, "snack"),
        DummyFoodItem(4, "Rajma Chawal", 480, 15.0, 80, 8.0, 60.0, "lunch")
    ]

    # Breakfast slot ranking
    bf_ranked = hybrid_recommender.score_and_rank_foods(food_list, profile, target_macros, meal_type="breakfast")
    assert bf_ranked[0]["food"].category == "breakfast"

    # Lunch slot ranking
    lunch_ranked = hybrid_recommender.score_and_rank_foods(food_list, profile, target_macros, meal_type="lunch")
    assert lunch_ranked[0]["food"].category in ["lunch", "dinner"]

    # Snack slot ranking
    snack_ranked = hybrid_recommender.score_and_rank_foods(food_list, profile, target_macros, meal_type="snack")
    assert snack_ranked[0]["food"].category in ["snack", "breakfast"]


def test_7day_planner_ux_fix():
    """Verify Issue 4 Fix: 7-day planner generates realistic 4-meal days and includes validation_report."""
    token = create_access_token(user_id=1, email="test@nutritwin.ai")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"start_date": "2026-08-29", "num_days": 7}
    res = client.post("/api/v1/optimize/7-day-plan", headers=headers, json=payload)
    assert res.status_code == 200, f"7-day plan creation failed: {res.text}"

    data = res.json()
    assert "validation_report" in data
    v_report = data["validation_report"]

    assert "total_weekly_cost_inr" in v_report
    assert "budget_compliant" in v_report
    assert "missing_meals_count" in v_report
    assert "repeated_meals_count" in v_report
    assert "validation_status" in v_report
    assert v_report["missing_meals_count"] == 0
    assert len(data["days"]) == 7
