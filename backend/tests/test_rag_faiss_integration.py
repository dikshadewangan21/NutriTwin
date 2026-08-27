import pytest
from app.services.rag_assistant import rag_assistant

class MockUserProfile:
    full_name = "Test Patient"
    fitness_goal = "health"
    dietary_preference = "vegetarian"
    daily_budget_inr = 300.0
    medical_conditions = ["diabetes", "kidney_disease"]
    target_calories = 2000.0
    target_protein_g = 80.0
    current_weight_kg = 70.0
    height_cm = 170.0
    age = 30

class MockFoodItem:
    def __init__(self, name, cal, pro, carbs, fat, cost, cat="lunch", pref="vegetarian", gi="Low"):
        self.name = name
        self.serving_unit = "1 portion"
        self.serving_weight_g = 150
        self.calories = cal
        self.protein_g = pro
        self.carbs_g = carbs
        self.fat_g = fat
        self.fiber_g = 4.0
        self.approx_cost_inr = cost
        self.category = cat
        self.dietary_type = pref
        self.glycemic_index = gi
        self.ingredients = [name.lower()]
        self.description = f"Healthy {name}"

def test_faiss_rag_retrieval_and_attribution():
    profile = MockUserProfile()
    food_list = [
        MockFoodItem("Boiled Sprouted Moong", 150, 12, 22, 2, 25),
        MockFoodItem("Vegetable Soup", 110, 4, 18, 2, 35)
    ]

    # Test 1: Diabetes & Kidney Query ground in NIDDK document chunks
    query1 = "What food choices help manage chronic kidney disease and protect kidneys?"
    res1 = rag_assistant.process_chat_query(query1, profile, None, food_list)
    
    assert "response" in res1
    assert "retrieved_context" in res1
    assert res1["retrieved_context"].get("rag_grounded") is True
    assert len(res1["retrieved_context"].get("rag_sources", [])) > 0
    assert "[Source: NIDDK" in res1["response"]

    # Test 2: Pain relievers / OTC medicine question
    query2 = "What over the counter pain relievers cause damage to kidneys?"
    res2 = rag_assistant.process_chat_query(query2, profile, None, food_list)
    
    assert "response" in res2
    assert "[Source: NIDDK" in res2["response"]
    assert "NSAIDs" in res2["response"] or "medicines" in res2["response"].lower()

def test_schema_preservation():
    profile = MockUserProfile()
    food_list = [MockFoodItem("Sprouted Moong", 150, 12, 22, 2, 25)]

    res = rag_assistant.process_chat_query("What should I eat today?", profile, None, food_list)
    assert set(res.keys()) == {"response", "intent_detected", "retrieved_context", "suggested_chips"}
