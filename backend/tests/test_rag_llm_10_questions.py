import sys
from pathlib import Path

# Ensure UTF-8 output encoding for Windows stdout
sys.stdout.reconfigure(encoding='utf-8')

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.rag_assistant import rag_assistant

class MockUserProfile:
    full_name = "Alex"
    fitness_goal = "health"
    dietary_preference = "vegetarian"
    daily_budget_inr = 300.0
    medical_conditions = ["diabetes", "kidney_disease", "hypertension"]
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

def run_10_rag_questions_test():
    profile = MockUserProfile()
    food_list = [
        MockFoodItem("Sprouted Moong Salad", 150, 12, 22, 2, 25),
        MockFoodItem("Oats Porridge", 180, 8, 30, 3, 30),
        MockFoodItem("Paneer Tikka", 250, 18, 8, 16, 75)
    ]

    questions = [
        # Category 1: Diabetes
        "What meal plans or food choices are recommended for people with diabetes?",
        "What health problems can occur if blood glucose remains too high over time?",
        
        # Category 2: Kidney Disease
        "How can I protect my kidneys from damage if I have chronic kidney disease?",
        "What are the warning signs or symptoms of early kidney disease?",
        "Why are NSAIDs and over the counter pain relievers dangerous for kidney function?",

        # Category 3: General Nutrition
        "What role do food and beverages play in managing health and reducing disease risk?",
        "How many hours of sleep should a healthy adult aim for each night?",
        
        # Category 4: Hypertension & Blood Pressure
        "How does high blood pressure damage kidneys and how can blood pressure be controlled?",
        "What blood pressure medicines like ACE inhibitors and ARBs help protect kidneys?",
        "What lifestyle habits keep kidneys and heart safe when dealing with hypertension?"
    ]

    print("\n" + "=" * 90)
    print("PHASE 9 — STEP 3: TESTING RAG ASSISTANT WITH 10 COMPREHENSIVE QUESTIONS")
    print("=" * 90)

    for i, q in enumerate(questions, 1):
        res = rag_assistant.process_chat_query(q, profile, None, food_list)
        sources = res.get("retrieved_context", {}).get("rag_sources", [])
        
        print(f"\n[{i}/10] QUESTION: \"{q}\"")
        print("-" * 90)

        if sources:
            print("RETRIEVED SOURCES:")
            seen_src = set()
            for s in sources:
                src_str = f"• {s.get('source')} | Title: \"{s.get('title')}\" | File: {s.get('original_file')} | URL: {s.get('source_url')}"
                if src_str not in seen_src:
                    seen_src.add(src_str)
                    print(f"  {src_str}")
        else:
            print("RETRIEVED SOURCES: None (SQL / Direct Response)")

        print("\nGENERATED GROUNDED ANSWER:")
        print(res.get("response", "").strip())
        print("=" * 90)

if __name__ == "__main__":
    run_10_rag_questions_test()
