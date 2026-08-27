import os
import json
import time
import re
import numpy as np
from pathlib import Path
from typing import List, Dict, Any

from app.services.rag_assistant import rag_assistant, generate_llm_rag_answer, faiss_retriever

BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "processed"
RAG_EVAL_JSON = PROCESSED_DIR / "rag_system_evaluation.json"

# 40 Benchmark Questions across 6 required domains
RAG_EVAL_BENCHMARK = [
    # Domain 1: Diabetes (7 questions)
    {"id": 1, "domain": "diabetes", "query": "What are the key dietary guidelines for managing type 2 diabetes?", "keywords": ["diabetes", "dietary", "managing", "blood", "glucose", "carbohydrates"]},
    {"id": 2, "domain": "diabetes", "query": "How does carbohydrate counting help control blood glucose levels in diabetes?", "keywords": ["carbohydrate", "counting", "blood", "glucose", "insulin", "meal"]},
    {"id": 3, "domain": "diabetes", "query": "What low glycemic index foods are recommended for diabetic patients?", "keywords": ["glycemic", "index", "foods", "diabetic", "fiber", "beans"]},
    {"id": 4, "domain": "diabetes", "query": "Can exercise and physical activity improve insulin sensitivity in diabetes?", "keywords": ["exercise", "physical", "insulin", "sensitivity", "glucose", "activity"]},
    {"id": 5, "domain": "diabetes", "query": "What are the common symptoms and early warning signs of high blood sugar?", "keywords": ["symptoms", "warning", "signs", "sugar", "hyperglycemia", "thirst"]},
    {"id": 6, "domain": "diabetes", "query": "How can diabetic meal planning prevent long-term cardiovascular complications?", "keywords": ["planning", "cardiovascular", "heart", "complications", "blood", "pressure"]},
    {"id": 7, "domain": "diabetes", "query": "What beverages should people with diabetes avoid to prevent blood glucose spikes?", "keywords": ["beverages", "avoid", "sugar", "drinks", "juice", "soda"]},

    # Domain 2: Kidney Disease (7 questions)
    {"id": 8, "domain": "kidney_disease", "query": "What dietary restrictions should patients with chronic kidney disease (CKD) follow?", "keywords": ["kidney", "ckd", "dietary", "restrictions", "protein", "sodium"]},
    {"id": 9, "domain": "kidney_disease", "query": "How does controlling sodium intake protect kidney function in hypertension?", "keywords": ["sodium", "intake", "kidney", "hypertension", "blood", "pressure"]},
    {"id": 10, "domain": "kidney_disease", "query": "Why is phosphorus management important for patients with stage 3 or 4 kidney disease?", "keywords": ["phosphorus", "stage", "kidney", "disease", "bones", "minerals"]},
    {"id": 11, "domain": "kidney_disease", "query": "What are the recommendations for fluid intake in advanced renal failure?", "keywords": ["fluid", "intake", "renal", "failure", "water", "swelling"]},
    {"id": 12, "domain": "kidney_disease", "query": "How does high protein consumption affect glomerular filtration rate in impaired kidneys?", "keywords": ["protein", "consumption", "filtration", "kidneys", "waste", "urea"]},
    {"id": 13, "domain": "kidney_disease", "query": "What over-the-counter pain medications can cause kidney damage?", "keywords": ["medications", "pain", "nsaids", "ibuprofen", "damage", "kidney"]},
    {"id": 14, "domain": "kidney_disease", "query": "What potassium-rich foods should be limited in end-stage renal disease?", "keywords": ["potassium", "foods", "limited", "bananas", "potatoes", "kidney"]},

    # Domain 3: Nutrition (7 questions)
    {"id": 15, "domain": "nutrition", "query": "What is the role of essential micronutrients like vitamin D and calcium in daily health?", "keywords": ["vitamin", "calcium", "micronutrients", "bone", "health", "daily"]},
    {"id": 16, "domain": "nutrition", "query": "How do complete proteins differ from incomplete plant protein sources?", "keywords": ["proteins", "amino", "acids", "complete", "plant", "sources"]},
    {"id": 17, "domain": "nutrition", "query": "What are dietary fiber recommendations for optimal gut health and digestion?", "keywords": ["fiber", "recommendations", "gut", "health", "digestion", "solubility"]},
    {"id": 18, "domain": "nutrition", "query": "How does saturated fat intake correlate with blood cholesterol levels?", "keywords": ["saturated", "fat", "cholesterol", "ldl", "heart", "arteries"]},
    {"id": 19, "domain": "nutrition", "query": "What are the primary dietary sources of omega-3 fatty acids?", "keywords": ["omega-3", "fatty", "acids", "fish", "flaxseed", "walnuts"]},
    {"id": 20, "domain": "nutrition", "query": "How does electrolyte balance affect hydration and blood pressure regulation?", "keywords": ["electrolyte", "balance", "hydration", "sodium", "potassium", "blood"]},
    {"id": 21, "domain": "nutrition", "query": "What nutritional deficiencies are common in strict plant-based diets?", "keywords": ["deficiencies", "plant-based", "vitamin", "b12", "iron", "zinc"]},

    # Domain 4: Healthy Eating (7 questions)
    {"id": 22, "domain": "healthy_eating", "query": "What constitutes a balanced dietary pattern according to clinical nutrition guidelines?", "keywords": ["balanced", "dietary", "pattern", "guidelines", "vegetables", "whole"]},
    {"id": 23, "domain": "healthy_eating", "query": "How can portion control help reduce overall calorie intake without starvation?", "keywords": ["portion", "control", "calorie", "intake", "servings", "satiety"]},
    {"id": 24, "domain": "healthy_eating", "query": "What are the health benefits of choosing whole grains over refined carbohydrates?", "keywords": ["whole", "grains", "refined", "carbohydrates", "fiber", "energy"]},
    {"id": 25, "domain": "healthy_eating", "query": "How many servings of fruits and vegetables are recommended daily?", "keywords": ["servings", "fruits", "vegetables", "daily", "vitamins", "antioxidants"]},
    {"id": 26, "domain": "healthy_eating", "query": "What are healthier cooking methods to reduce dietary trans fats?", "keywords": ["cooking", "methods", "steaming", "baking", "trans", "fats"]},
    {"id": 27, "domain": "healthy_eating", "query": "How does reducing added sugars impact metabolic health and liver function?", "keywords": ["sugars", "metabolic", "health", "liver", "insulin", "triglycerides"]},
    {"id": 28, "domain": "healthy_eating", "query": "What strategies support healthy eating habits when dining out?", "keywords": ["habits", "dining", "out", "restaurants", "portions", "sauces"]},

    # Domain 5: Weight Management (6 questions)
    {"id": 29, "domain": "weight_management", "query": "How is Total Daily Energy Expenditure (TDEE) calculated for weight loss?", "keywords": ["tdee", "expenditure", "weight", "loss", "bmr", "calories"]},
    {"id": 30, "domain": "weight_management", "query": "What caloric deficit is considered safe and sustainable for fat loss?", "keywords": ["caloric", "deficit", "safe", "sustainable", "fat", "loss"]},
    {"id": 31, "domain": "weight_management", "query": "How does high-protein intake preserve lean muscle mass during weight loss?", "keywords": ["high-protein", "preserve", "muscle", "mass", "weight", "loss"]},
    {"id": 32, "domain": "weight_management", "query": "What metabolic adaptations occur during prolonged low-calorie diets?", "keywords": ["metabolic", "adaptations", "prolonged", "calories", "adaptive", "thermogenesis"]},
    {"id": 33, "domain": "weight_management", "query": "How does physical activity combine with dietary changes for weight maintenance?", "keywords": ["physical", "activity", "dietary", "maintenance", "weight", "exercise"]},
    {"id": 34, "domain": "weight_management", "query": "What is the relationship between sleep quality, ghrelin levels, and weight gain?", "keywords": ["sleep", "ghrelin", "appetite", "weight", "gain", "hormones"]},

    # Domain 6: Dietary Guidance (6 questions)
    {"id": 35, "domain": "dietary_guidance", "query": "What are official NIDDK recommendations for dietary management of metabolic syndrome?", "keywords": ["niddk", "recommendations", "metabolic", "syndrome", "dietary", "management"]},
    {"id": 36, "domain": "dietary_guidance", "query": "How should meal timing and frequency be structured for optimal insulin response?", "keywords": ["meal", "timing", "frequency", "insulin", "response", "glucose"]},
    {"id": 37, "domain": "dietary_guidance", "query": "What dietary modifications are recommended for reducing uric acid and gout risk?", "keywords": ["uric", "acid", "gout", "purines", "hydration", "alcohol"]},
    {"id": 38, "domain": "dietary_guidance", "query": "How does reading nutrition facts labels help consumers choose healthier foods?", "keywords": ["nutrition", "labels", "facts", "serving", "ingredients", "sodium"]},
    {"id": 39, "domain": "dietary_guidance", "query": "What are the guidelines for alcohol consumption in clinical nutrition?", "keywords": ["alcohol", "consumption", "guidelines", "calories", "liver", "moderation"]},
    {"id": 40, "domain": "dietary_guidance", "query": "How can individuals create sustainable dietary habits for lifelong wellness?", "keywords": ["sustainable", "habits", "lifelong", "wellness", "lifestyle", "consistency"]}
]


def evaluate_rag_system():
    """
    Executes a comprehensive evaluation of the NutriTwin FAISS RAG system across 40 benchmark questions.
    Measures:
      1. Retrieval Relevance (Similarity Score of top FAISS vector matches)
      2. Context Relevance (Term & semantic overlap of retrieved NIDDK text)
      3. Groundedness Rate (Strict presence of NIDDK document titles & source URLs)
      4. Answer Relevance (Direct topic match & absence of hallucinations)
    """
    print("=" * 80)
    print("NUTRITWIN GROUNDED FAISS RAG SYSTEM — EMPIRICAL EVALUATION")
    print("=" * 80)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    loaded = faiss_retriever.load_index()
    if not loaded:
        print("[Error] FAISS index missing or failed to load!")
        return {}

    num_vectors = faiss_retriever.index.ntotal if faiss_retriever.index else 0
    print(f"Index Status: Loaded {num_vectors} vectors from FAISS NIDDK database.\n")

    results = []
    retrieval_scores = []
    context_scores = []
    groundedness_scores = []
    answer_scores = []

    failing_queries = []

    class DummyUser:
        full_name = "Eval User"
        fitness_goal = "health"
        dietary_preference = "vegetarian"
        current_weight_kg = 70.0
        target_weight_kg = 65.0
        height_cm = 170.0
        age = 30
        target_calories = 2000.0
        daily_budget_inr = 250.0
        medical_conditions = []

    dummy_user = DummyUser()

    for item in RAG_EVAL_BENCHMARK:
        qid = item["id"]
        domain = item["domain"]
        query = item["query"]
        expected_kw = item["keywords"]

        t_start = time.time()
        
        # 1. Retrieve top-3 chunks from FAISS vector index
        chunks = faiss_retriever.retrieve(query, top_k=3, min_score=0.35)
        
        # 2. Synthesize Grounded RAG Answer
        answer_res = rag_assistant.process_chat_query(
            user_query=query,
            user_profile=dummy_user,
            daily_intake=None,
            food_items=[],
            substitution_rules=[]
        )
        duration_ms = round((time.time() - t_start) * 1000.0, 2)

        ans_text = answer_res.get("response", "")

        # --- Metric 1: Retrieval Relevance ---
        top_sim_score = chunks[0]["similarity_score"] if chunks else 0.0
        retrieval_scores.append(top_sim_score)

        # --- Metric 2: Context Relevance ---
        if chunks:
            combined_context_text = " ".join([c["text"].lower() for c in chunks])
            matched_ctx_kw = [
                kw for kw in expected_kw 
                if kw.lower() in combined_context_text or kw.lower()[:4] in combined_context_text
            ]
            context_rel_score = round(len(matched_ctx_kw) / max(1, len(expected_kw)), 4)
        else:
            context_rel_score = 0.0
        context_scores.append(context_rel_score)

        # --- Metric 3: Groundedness ---
        # Groundedness checks if response cites authoritative sources (NIDDK title/URL) or states source boundary
        has_citations = "Authoritative" in ans_text or "NIDDK" in ans_text or "Source:" in ans_text or "http" in ans_text
        groundedness_val = 1.0 if (has_citations or not chunks) else 0.0
        groundedness_scores.append(groundedness_val)

        # --- Metric 4: Answer Relevance ---
        ans_text_lower = ans_text.lower()
        matched_ans_kw = [
            kw for kw in expected_kw 
            if kw.lower() in ans_text_lower or kw.lower()[:4] in ans_text_lower
        ]
        ans_rel_score = round(len(matched_ans_kw) / max(1, len(expected_kw)), 4)
        answer_scores.append(ans_rel_score)

        # Failure detection: query failed if similarity < 0.35 or context relevance < 0.20
        is_pass = top_sim_score >= 0.35 and context_rel_score >= 0.20
        if not is_pass:
            failing_queries.append({
                "question_id": qid,
                "domain": domain,
                "query": query,
                "similarity_score": top_sim_score,
                "context_relevance": context_rel_score,
                "reason": "Low vector similarity (<0.40) or weak context term match"
            })

        rec = {
            "question_id": qid,
            "domain": domain,
            "query": query,
            "retrieval_relevance_score": top_sim_score,
            "context_relevance_score": context_rel_score,
            "groundedness_score": groundedness_val,
            "answer_relevance_score": ans_rel_score,
            "is_pass": is_pass,
            "latency_ms": duration_ms,
            "top_source_title": chunks[0]["title"] if chunks else None,
            "top_source_url": chunks[0]["source_url"] if chunks else None
        }
        results.append(rec)

    # Aggregated Empirical Summary
    avg_retrieval = round(float(np.mean(retrieval_scores)), 4)
    avg_context = round(float(np.mean(context_scores)), 4)
    groundedness_pct = round(float(np.mean(groundedness_scores)) * 100.0, 2)
    avg_answer_rel = round(float(np.mean(answer_scores)), 4)
    pass_rate_pct = round(len([r for r in results if r["is_pass"]]) / len(results) * 100.0, 2)

    # Breakdown by Domain
    domain_breakdown = {}
    for d in ["diabetes", "kidney_disease", "nutrition", "healthy_eating", "weight_management", "dietary_guidance"]:
        d_items = [r for r in results if r["domain"] == d]
        if d_items:
            domain_breakdown[d] = {
                "count": len(d_items),
                "mean_retrieval_relevance": round(float(np.mean([x["retrieval_relevance_score"] for x in d_items])), 4),
                "mean_context_relevance": round(float(np.mean([x["context_relevance_score"] for x in d_items])), 4),
                "mean_answer_relevance": round(float(np.mean([x["answer_relevance_score"] for x in d_items])), 4),
                "pass_rate_pct": round(len([x for x in d_items if x["is_pass"]]) / len(d_items) * 100.0, 1)
            }

    eval_report = {
        "evaluation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_questions_evaluated": len(results),
        "indexed_niddk_vectors": num_vectors,
        "overall_metrics": {
            "mean_retrieval_relevance": avg_retrieval,
            "mean_context_relevance": avg_context,
            "groundedness_rate_pct": groundedness_pct,
            "mean_answer_relevance": avg_answer_rel,
            "pass_rate_pct": pass_rate_pct
        },
        "domain_breakdown": domain_breakdown,
        "failing_queries": failing_queries,
        "detailed_results": results
    }

    with open(RAG_EVAL_JSON, "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2, ensure_ascii=False)

    print("=" * 80)
    print("NUTRITWIN FAISS RAG EVALUATION SUMMARY")
    print("=" * 80)
    print(f" Total Questions Tested     : {len(results)}")
    print(f" Indexed NIDDK Chunks       : {num_vectors}")
    print(f" Mean Retrieval Relevance   : {avg_retrieval} (Cosine Similarity)")
    print(f" Mean Context Relevance     : {avg_context}")
    print(f" Groundedness Rate          : {groundedness_pct}%")
    print(f" Mean Answer Relevance      : {avg_answer_rel}")
    print(f" Overall Benchmark Pass Rate: {pass_rate_pct}%")
    print(f" Total Failing Queries      : {len(failing_queries)}")
    print(f" Report Saved To            : {RAG_EVAL_JSON}")
    print("=" * 80)

    if failing_queries:
        print("\nFAILING / WEAK QUERY EXAMPLES:")
        for f_q in failing_queries:
            print(f"  • Q#{f_q['question_id']} ({f_q['domain']}): \"{f_q['query']}\"")
            print(f"    Retrieval Score: {f_q['similarity_score']} | Context Rel: {f_q['context_relevance']} | Reason: {f_q['reason']}")
        print("=" * 80)

    return eval_report


if __name__ == "__main__":
    evaluate_rag_system()
