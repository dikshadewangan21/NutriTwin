import pytest
from app.services.rag_assistant import rag_assistant
from app.models.food import FoodItem

class MockUserProfile:
    full_name = "Test User"
    fitness_goal = "weight_loss"
    dietary_preference = "vegetarian"
    daily_budget_inr = 250.0
    medical_conditions = ["diabetes"]
    target_calories = 1800.0
    target_protein_g = 90.0

class MockFoodItem:
    def __init__(self, name, cal, pro, carbs, fat, cost, cat, pref="vegetarian", gi="Low"):
        self.name = name
        self.serving_unit = "1 bowl"
        self.calories = cal
        self.protein_g = pro
        self.carbs_g = carbs
        self.fat_g = fat
        self.fiber_g = 3.0
        self.approx_cost_inr = cost
        self.category = cat
        self.dietary_type = pref
        self.glycemic_index = gi
        self.ingredients = [name.lower()]
        self.description = f"Fresh {name}"

def test_dynamic_rag_assistant_queries():
    profile = MockUserProfile()
    food_list = [
        MockFoodItem("Paneer Bhurji", 280, 22, 10, 18, 70, "dinner"),
        MockFoodItem("Sprouted Moong Salad", 180, 14, 25, 3, 35, "lunch"),
        MockFoodItem("Oats Porridge", 210, 10, 36, 4, 30, "breakfast"),
        MockFoodItem("Grilled Tofu Tikka", 220, 20, 8, 12, 85, "dinner", "vegan")
    ]

    # Test 1: Budget query
    res1 = rag_assistant.process_chat_query("What can I eat under 50 rupees?", profile, None, food_list)
    assert "response" in res1
    assert "budget" in res1["intent_detected"].lower()

    # Test 2: Replacement query
    res2 = rag_assistant.process_chat_query("What can I replace paneer with?", profile, None, food_list)
    assert "response" in res2
    assert "substitution" in res2["intent_detected"].lower()

    # Test 3: Health condition query
    res3 = rag_assistant.process_chat_query("What should I eat for diabetes and PCOS?", profile, None, food_list)
    assert "response" in res3
    assert "diabetes" in res3["response"].lower() or "guidance" in res3["intent_detected"].lower()

    # Test 4: Dynamic arbitrary question
    res4 = rag_assistant.process_chat_query("Why is protein important for fat loss?", profile, None, food_list)
    assert "response" in res4
    assert len(res4["response"]) > 50
    assert "suggested_chips" in res4
