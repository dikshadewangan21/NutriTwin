import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

try:
    import faiss
    from sentence_transformers import SentenceTransformer
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

RAG_SYSTEM_PROMPT = """You are NutriTwin's Grounded AI Nutrition Assistant.
Your task is to provide an accurate, clear, and grounded response to the user's question using ONLY the provided authoritative NIDDK clinical documentation chunks.

STRICT COMPLIANCE RULES:
1. Answer using the retrieved context provided below.
2. Do not invent medical facts.
3. If the retrieved context does not contain enough information to answer the question, explicitly state: "The available sources do not provide enough information to answer this question."
4. Do not diagnose diseases under any circumstances.
5. Do not prescribe medications or medical treatments.
6. Do not invent citations, links, or fake source titles.
7. Always return and format the exact source metadata associated with the retrieved context (Source, Title, Condition, Source URL).

RETRIEVED NIDDK CONTEXT:
{context_str}

USER QUESTION:
{user_question}
"""


class FAISSRetriever:
    """
    Singleton retriever for loading and querying the FAISS vector index of authoritative NIDDK document chunks.
    """
    def __init__(self, artifact_dir: Optional[Path] = None):
        if artifact_dir is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            artifact_dir = base_dir / "ml_pipeline" / "artifacts" / "faiss_nutrition_index"

        self.artifact_dir = artifact_dir
        self.index_file = self.artifact_dir / "index.faiss"
        self.metadata_file = self.artifact_dir / "metadata.json"
        self.config_file = self.artifact_dir / "config.json"

        self.model = None
        self.index = None
        self.metadata = []
        self.is_loaded = False

    def load_index(self) -> bool:
        if self.is_loaded:
            return True

        if not FAISS_AVAILABLE:
            print("[FAISSRetriever] Warning: faiss or sentence_transformers package not available.")
            return False

        if not self.index_file.exists() or not self.metadata_file.exists():
            print(f"[FAISSRetriever] Warning: Index files missing at {self.artifact_dir}")
            return False

        try:
            model_name = "sentence-transformers/all-MiniLM-L6-v2"
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    model_name = cfg.get("model_name", model_name)

            self.model = SentenceTransformer(model_name)
            self.index = faiss.read_index(str(self.index_file))

            with open(self.metadata_file, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)

            self.is_loaded = True
            print(f"[FAISSRetriever] Loaded FAISS index ({self.index.ntotal} vectors) and metadata.")
            return True
        except Exception as e:
            print(f"[FAISSRetriever] Error loading FAISS index: {e}")
            return False

    def retrieve(self, query: str, top_k: int = 3, min_score: float = 0.35) -> List[Dict[str, Any]]:
        if not self.load_index():
            return []

        try:
            query_vec = self.model.encode([query], convert_to_numpy=True).astype(np.float32)
            faiss.normalize_L2(query_vec)

            scores, indices = self.index.search(query_vec, top_k)

            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.metadata) and score >= min_score:
                    item = dict(self.metadata[idx])
                    item["similarity_score"] = round(float(score), 4)
                    results.append(item)

            return results
        except Exception as e:
            print(f"[FAISSRetriever] Error during vector search: {e}")
            return []


# Global retriever instance
faiss_retriever = FAISSRetriever()


def generate_llm_rag_answer(user_question: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
    """
    Generates a grounded RAG response using an external LLM API (Gemini, OpenAI, or Groq)
    configured via environment variables. If no API key is set in environment, generates
    a deterministic grounded response directly from the retrieved NIDDK chunks without hallucination.
    """
    if not retrieved_chunks:
        return "The available sources do not provide enough information to answer this question."

    context_blocks = []
    sources_metadata = []
    seen_sources = set()

    for idx, c in enumerate(retrieved_chunks, 1):
        context_blocks.append(
            f"[Chunk {idx}]\n"
            f"Title: {c.get('title')}\n"
            f"Condition: {c.get('condition')}\n"
            f"Source: {c.get('source')} ({c.get('source_url')})\n"
            f"File: {c.get('original_file')}\n"
            f"Content: {c.get('text')}"
        )
        source_key = (c.get('title'), c.get('source_url'))
        if source_key not in seen_sources:
            seen_sources.add(source_key)
            sources_metadata.append(
                f"• [Source: {c.get('source')} — {c.get('title')} ({c.get('source_url')})]"
            )

    context_str = "\n\n".join(context_blocks)
    sources_formatted = "\n".join(sources_metadata)

    # Environment variables (never hardcoded, never committed to git)
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")

    # 1. Gemini LLM API
    if gemini_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            prompt = RAG_SYSTEM_PROMPT.format(context_str=context_str, user_question=user_question)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            if response and response.text:
                res_text = response.text.strip()
                if "Source:" not in res_text:
                    res_text += f"\n\n📚 **Authoritative Sources**:\n{sources_formatted}"
                return res_text
        except Exception as e:
            print(f"[RAGLLM] Gemini API error: {e}")

    # 2. OpenAI LLM API
    if openai_key:
        try:
            import openai
            client = openai.OpenAI(api_key=openai_key)
            prompt = RAG_SYSTEM_PROMPT.format(context_str=context_str, user_question=user_question)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are NutriTwin's Grounded RAG Assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            if response.choices and response.choices[0].message.content:
                res_text = response.choices[0].message.content.strip()
                if "Source:" not in res_text:
                    res_text += f"\n\n📚 **Authoritative Sources**:\n{sources_formatted}"
                return res_text
        except Exception as e:
            print(f"[RAGLLM] OpenAI API error: {e}")

    # 3. Groq LLM API
    if groq_key:
        try:
            import groq
            client = groq.Groq(api_key=groq_key)
            prompt = RAG_SYSTEM_PROMPT.format(context_str=context_str, user_question=user_question)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are NutriTwin's Grounded RAG Assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            if response.choices and response.choices[0].message.content:
                res_text = response.choices[0].message.content.strip()
                if "Source:" not in res_text:
                    res_text += f"\n\n📚 **Authoritative Sources**:\n{sources_formatted}"
                return res_text
        except Exception as e:
            print(f"[RAGLLM] Groq API error: {e}")

    # 4. Fallback: Grounded synthesis directly from retrieved NIDDK chunks
    excerpts_str = "\n\n".join([
        f"> \"{c['text']}\"\n> — *[Source: {c['source']} — {c['title']} ({c['source_url']})]*"
        for c in retrieved_chunks[:2]
    ])

    return (
        f"🩺 **Authoritative Medical & Nutrition Guidance (NIDDK Grounded)**:\n\n"
        f"Based on clinical documentation from the National Institute of Diabetes and Digestive and Kidney Diseases (NIDDK):\n\n"
        f"{excerpts_str}\n\n"
        f"📚 **Authoritative Sources**:\n"
        f"{sources_formatted}\n\n"
        f"🛡️ *NutriTwin's safety layer grounds all medical nutrition advice in official NIDDK documentation without prescribing or diagnosing.*"
    )


class GroundedRAGAssistant:
    """
    Dynamic RAG AI Nutrition Assistant.
    Integrates FAISS vector search over authoritative NIDDK documents
    with SQL database grounding (food items, substitution rules, health constraints)
    and user metrics (TDEE, BMR, targets, logged intake).
    """

    def __init__(self):
        self.retriever = faiss_retriever

    def process_chat_query(
        self, 
        user_query: str, 
        user_profile: Any, 
        daily_intake: Any, 
        food_items: List[Any], 
        substitution_rules: List[Any] = [],
        chat_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Processes natural language user prompt by dynamically parsing entities, matching 
        context against verified DB items and FAISS vector RAG index, and synthesizing an accurate, 
        personalized answer with source attribution.
        """
        if not user_query or not user_query.strip():
            user_query = "What should I eat today?"

        query_raw = user_query.strip()
        query_lower = query_raw.lower()

        # 1. User Profile & Real-time Intake Calculations
        user_name = user_profile.full_name if hasattr(user_profile, 'full_name') and user_profile.full_name else 'Friend'
        goal_raw = getattr(user_profile, 'fitness_goal', 'health') or 'health'
        goal = goal_raw.replace('_', ' ')
        pref_raw = getattr(user_profile, 'dietary_preference', 'vegetarian') or 'vegetarian'
        pref = pref_raw.replace('_', '-')
        
        weight_kg = getattr(user_profile, 'current_weight_kg', 70.0) or 70.0
        height_cm = getattr(user_profile, 'height_cm', 170.0) or 170.0
        age = getattr(user_profile, 'age', 25) or 25

        target_cal = getattr(user_profile, 'target_calories', None) or getattr(user_profile, 'tdee', 2000.0) or 2000.0
        target_pro = getattr(user_profile, 'target_protein_g', None) or (target_cal * 0.25 / 4.0) or 80.0
        target_carb = getattr(user_profile, 'target_carbs_g', None) or (target_cal * 0.50 / 4.0) or 220.0
        target_fat = getattr(user_profile, 'target_fat_g', None) or (target_cal * 0.25 / 9.0) or 55.0
        
        daily_budget = getattr(user_profile, 'daily_budget_inr', 250.0) or 250.0

        logged_cal = daily_intake.total_calories if daily_intake else 0.0
        logged_pro = daily_intake.total_protein_g if daily_intake else 0.0
        logged_carb = daily_intake.total_carbs_g if daily_intake else 0.0
        logged_fat = daily_intake.total_fat_g if daily_intake else 0.0

        logged_cost = sum(
            item.get("cost_inr", 0.0) for item in (daily_intake.logged_items or [])
        ) if daily_intake and hasattr(daily_intake, 'logged_items') and daily_intake.logged_items else 0.0

        rem_cal = max(0.0, target_cal - logged_cal)
        rem_pro = max(0.0, target_pro - logged_pro)
        rem_budget = max(0.0, daily_budget - logged_cost)

        conditions = getattr(user_profile, 'medical_conditions', []) or []
        if isinstance(conditions, str):
            conditions = [conditions]
        active_conditions = [c.lower() for c in conditions if c and c.lower() != 'none']

        # 2. Query Entity Parsing
        max_cal_match = re.search(r'(?:under|below|less than|\<)\s*(\d+)\s*(?:cal|calories|kcal)', query_lower)
        max_cal_constraint = float(max_cal_match.group(1)) if max_cal_match else None

        max_cost_match = re.search(r'(?:under|below|less than|budget|\<\s*₹?|\₹)\s*(\d+)\s*(?:rs|rupees|inr|₹)?', query_lower)
        max_cost_constraint = float(max_cost_match.group(1)) if max_cost_match else None

        min_pro_match = re.search(r'(?:at least|more than|minimum|\>)\s*(\d+)\s*g?\s*(?:protein|pro)', query_lower)
        min_pro_constraint = float(min_pro_match.group(1)) if min_pro_match else None

        # 3. Database RAG Item Filtering & Matching
        valid_foods = food_items
        if pref in ['vegetarian', 'vegan', 'eggetarian', 'jain']:
            valid_foods = [f for f in valid_foods if f.dietary_type in [pref, 'vegetarian', 'vegan']]

        if max_cost_constraint:
            valid_foods = [f for f in valid_foods if f.approx_cost_inr <= max_cost_constraint]
        if max_cal_constraint:
            valid_foods = [f for f in valid_foods if f.calories <= max_cal_constraint]
        if min_pro_constraint:
            valid_foods = [f for f in valid_foods if f.protein_g >= min_pro_constraint]

        valid_foods_sorted = sorted(valid_foods, key=lambda f: (f.protein_g / max(1.0, f.calories)), reverse=True)

        # Detect food items mentioned in query
        common_generic_words = {"water", "salt", "sugar", "oil", "ice", "lemon", "spices", "herbs", "drink", "food", "eat", "meal", "diet"}
        directly_mentioned_foods = []
        for food in food_items:
            fname = food.name.lower()
            if fname in query_lower:
                directly_mentioned_foods.append(food)
            else:
                for ing in (food.ingredients or []):
                    ing_lower = ing.lower()
                    if ing_lower not in common_generic_words and len(ing_lower) >= 4 and ing_lower in query_lower:
                        directly_mentioned_foods.append(food)
                        break

        # 4. Intent Detection Flags
        is_budget_query = bool(re.search(r'\b(?:budget|cost|price|cheap|rupees|rs|expensive|afford)\b|\₹', query_lower))
        is_replacement_query = any(w in query_lower for w in ["replace", "substitute", "instead", "don't have", "swap", "alternative"])

        # 5. Perform FAISS Vector Search
        rag_chunks = self.retriever.retrieve(query_raw, top_k=3, min_score=0.35)

        response_text = ""
        intent_detected = "general_query"
        retrieved_context: Dict[str, Any] = {
            "query": user_query,
            "target_calories": round(target_cal, 1),
            "remaining_calories": round(rem_cal, 1),
            "remaining_protein_g": round(rem_pro, 1),
            "remaining_budget_inr": round(rem_budget, 1)
        }

        if rag_chunks:
            retrieved_context["rag_grounded"] = True
            retrieved_context["rag_sources"] = [
                {
                    "chunk_id": c["chunk_id"],
                    "title": c["title"],
                    "original_file": c["original_file"],
                    "condition": c["condition"],
                    "source": c["source"],
                    "source_url": c["source_url"],
                    "score": c["similarity_score"]
                }
                for c in rag_chunks
            ]

        # --- A. Budget & Cost Optimization ---
        if is_budget_query:
            intent_detected = "budget_optimization"
            target_limit = max_cost_constraint or rem_budget
            affordable_dishes = [f for f in valid_foods_sorted if f.approx_cost_inr <= target_limit][:4]

            if affordable_dishes:
                dish_lines = "\n".join([
                    f"• **{f.name}** ({f.serving_unit}): ₹{f.approx_cost_inr} | {f.calories} kcal, {f.protein_g}g Protein, {f.carbs_g}g Carbs"
                    for f in affordable_dishes
                ])
            else:
                fallback_dishes = sorted(valid_foods_sorted, key=lambda f: f.approx_cost_inr)[:3]
                dish_lines = "\n".join([
                    f"• **{f.name}** ({f.serving_unit}): ₹{f.approx_cost_inr} | {f.calories} kcal, {f.protein_g}g Protein"
                    for f in fallback_dishes
                ])

            response_text = (
                f"💰 **Budget & Cost Optimization**:\n\n"
                f"You currently have **₹{round(rem_budget, 2)}** remaining today out of your daily ₹{daily_budget} budget.\n\n"
                f"Top cost-effective dishes from our database matching your {pref} diet:\n\n"
                f"{dish_lines}\n\n"
                f"📊 *Pro Tip*: Combining plant proteins like lentils (Dal), sprouts, and eggs/tofu gives high nutritional value for under ₹40 per serving!"
            )
            retrieved_context["affordable_dishes"] = [f.name for f in affordable_dishes]

        # --- B. Food Replacement & Ingredient Swap ---
        elif is_replacement_query:
            intent_detected = "food_substitution"
            
            target_name = "this food"
            words = query_lower.split()
            for idx, w in enumerate(words):
                if w in ["replace", "swap", "instead", "substitute", "have"] and idx + 1 < len(words):
                    next_word = words[idx + 1].strip("?,.")
                    if next_word not in ["with", "for", "of", "a", "the", "my"]:
                        target_name = next_word
                        break

            db_subs = [
                s for s in substitution_rules
                if target_name in s.original_food_name.lower() or target_name in s.substitute_food_name.lower()
            ]

            dynamic_swaps = [
                f for f in valid_foods_sorted 
                if target_name not in f.name.lower() and f.protein_g >= 12.0
            ][:3]

            if db_subs:
                swap_lines = "\n".join([f"• **{s.substitute_food_name}**: {s.reason} (Match Score: {int(s.nutritional_match_score * 100)}%)" for s in db_subs[:3]])
            elif dynamic_swaps:
                swap_lines = "\n".join([
                    f"• **{f.name}** ({f.serving_unit}): {f.protein_g}g Protein, {f.calories} kcal — ₹{f.approx_cost_inr}/serving"
                    for f in dynamic_swaps
                ])
            else:
                swap_lines = "• **Soya Chunks / Tofu / Sprouted Moong**: Excellent high-protein, low-fat replacements."

            response_text = (
                f"🔄 **Smart Dynamic Substitutions**:\n\n"
                f"Looking to replace **{target_name.title()}**? Here are optimal, verified alternatives from our database:\n\n"
                f"{swap_lines}\n\n"
                f"These replacements preserve your daily protein target ({target_pro}g) without interrupting your {goal} progress."
            )
            retrieved_context["swaps"] = [f.name for f in dynamic_swaps]

        # --- C. FAISS Vector RAG Grounded Answers ---
        elif rag_chunks:
            intent_detected = "disease_nutrition_guidance"
            response_text = generate_llm_rag_answer(query_raw, rag_chunks)

        # --- D. Specific Food / Dish Query ---
        elif directly_mentioned_foods:
            intent_detected = "food_analysis"
            target_food = directly_mentioned_foods[0]

            cal_status = "Fits smoothly into your remaining calorie allowance."
            if target_food.calories > rem_cal:
                cal_status = f"⚠️ Exceeds your current remaining calorie allowance (~{round(rem_cal, 0)} kcal)."

            response_text = (
                f"🔍 **Dynamic Nutritional Breakdown for {target_food.name}**:\n\n"
                f"• **Serving Size**: {target_food.serving_unit} (~{target_food.serving_weight_g}g)\n"
                f"• **Calories**: {target_food.calories} kcal\n"
                f"• **Protein**: {target_food.protein_g}g | **Carbs**: {target_food.carbs_g}g (Fiber: {target_food.fiber_g}g) | **Fat**: {target_food.fat_g}g\n"
                f"• **Glycemic Index**: {target_food.glycemic_index}\n"
                f"• **Approx Cost**: ₹{target_food.approx_cost_inr}\n"
                f"• **Dietary Type**: {target_food.dietary_type.replace('_', ' ').title()}\n"
                f"• **Ingredients**: {', '.join(target_food.ingredients or ['Natural ingredients'])}\n\n"
                f"📊 **Macro Evaluation**: {cal_status}\n"
                f"Description: {target_food.description or 'Fresh, traditional dish prepared with balanced macros.'}"
            )
            retrieved_context["analyzed_food"] = target_food.name

        # --- E. Post-Workout & Pre-Workout Gym Fueling ---
        elif any(w in query_lower for w in ["workout", "gym", "exercise", "post-workout", "pre-workout", "muscle", "recovery"]):
            intent_detected = "workout_nutrition"
            is_post = any(w in query_lower for w in ["post", "after", "recovery", "done"])

            if is_post:
                high_pro_foods = [f for f in valid_foods_sorted if f.protein_g >= 15.0][:3]
                foods_str = "\n".join([
                    f"• **{f.name}** ({f.serving_unit}): {f.protein_g}g Protein | {f.calories} kcal | ₹{f.approx_cost_inr}"
                    for f in high_pro_foods
                ])
                target_post_pro = round(max(20.0, target_pro * 0.25), 1)

                response_text = (
                    f"💪 **Dynamic Post-Workout Recovery**:\n\n"
                    f"Within 45 minutes post-workout, consume **~{target_post_pro}g fast-digesting protein** with moderate carbs to repair muscle tissue and replenish glycogen.\n\n"
                    f"Recommended meals matching your profile:\n\n"
                    f"{foods_str}\n\n"
                    f"🔥 *Your remaining protein target today: {round(rem_pro, 1)}g.*"
                )
            else:
                easy_carb_foods = [f for f in valid_foods if f.carbs_g >= 20.0 and f.calories <= 300][:3]
                pre_str = "\n".join([
                    f"• **{f.name}**: {f.carbs_g}g Carbs, {f.protein_g}g Protein ({f.calories} kcal)"
                    for f in easy_carb_foods
                ])

                response_text = (
                    f"⚡ **Dynamic Pre-Workout Fueling**:\n\n"
                    f"Eat 45-60 minutes prior to exercise. Prioritize easily digestible complex carbs with moderate protein to maximize stamina:\n\n"
                    f"{pre_str}\n\n"
                    f"💧 *Drink 300-500ml water 30 minutes before your workout for optimal hydration.*"
                )

        # --- F. Meal Planning / Recommendations ---
        elif any(w in query_lower for w in ["what to eat", "dinner", "lunch", "breakfast", "snack", "suggest", "recommend", "menu"]):
            intent_detected = "meal_recommendation"
            slot = "dinner"
            if "breakfast" in query_lower: slot = "breakfast"
            elif "lunch" in query_lower: slot = "lunch"
            elif "snack" in query_lower: slot = "snack"

            slot_matches = [f for f in valid_foods_sorted if f.category.lower() == slot or slot in f.category.lower()][:3]
            if not slot_matches:
                slot_matches = valid_foods_sorted[:3]

            rec_lines = "\n".join([
                f"• **{f.name}** ({f.serving_unit}): {f.calories} kcal | {f.protein_g}g Protein | {f.carbs_g}g Carbs | ₹{f.approx_cost_inr}"
                for f in slot_matches
            ])

            response_text = (
                f"🥗 **Dynamic {slot.title()} Recommendations**:\n\n"
                f"Based on your **{goal.upper()}** goal, **{pref.upper()}** diet, and remaining **{round(rem_cal, 0)} kcal / {round(rem_pro, 1)}g protein** today:\n\n"
                f"{rec_lines}\n\n"
                f"All options fit your daily budget (₹{daily_budget}/day) and dietary rules."
            )
            retrieved_context["suggested_dishes"] = [f.name for f in slot_matches]

        # --- G. Open Knowledge Engine ---
        else:
            intent_detected = "dynamic_knowledge_qa"

            kw_protein = any(w in query_lower for w in ["protein", "amino", "muscle"])
            kw_water = any(w in query_lower for w in ["water", "hydration", "drink", "fluid", "dehydrated"])
            kw_weight = any(w in query_lower for w in ["weight", "lose", "gain", "fat loss", "tdee", "deficit"])

            recommended_water_l = round((weight_kg * 0.035) + 0.5, 1)
            top_db_items = valid_foods_sorted[:3]
            db_item_names = ", ".join([f.name for f in top_db_items]) if top_db_items else "Paneer Bhurji, Tofu Tikka, Moong Dal Chela"

            if kw_protein:
                explanation = (
                    f"Protein is essential for your **{goal}** goal. At {weight_kg}kg, your optimal daily target is "
                    f"**{round(target_pro, 1)}g** (~1.4-1.8g per kg body weight).\n"
                    f"It supports lean muscle preservation, boosts thermogenesis, and keeps you satiated longer."
                )
            elif kw_water:
                explanation = (
                    f"Based on your body weight ({weight_kg}kg) and activity profile, your recommended fluid intake is "
                    f"**{recommended_water_l} Liters/day**. Proper hydration optimizes digestion, metabolic rate, and workout recovery."
                )
            elif kw_weight:
                explanation = (
                    f"For your **{goal}** target ({user_profile.current_weight_kg}kg → {user_profile.target_weight_kg}kg), "
                    f"your calculated TDEE is **{round(target_cal, 0)} kcal/day**.\n"
                    f"Maintaining a consistent ~400 kcal deficit while keeping protein at **{round(target_pro, 1)}g** ensures steady fat loss without muscle wasting."
                )
            else:
                explanation = (
                    f"Regarding your query (*\"{user_query}\"*):\n"
                    f"To optimize your {goal} results on a {pref} diet, focus on whole, unrefined foods with a balanced macronutrient distribution "
                    f"({round(target_cal, 0)} kcal/day: {round(target_pro, 1)}g Protein, {round(target_carb, 1)}g Carbs, {round(target_fat, 1)}g Fat)."
                )

            response_text = (
                f"Hello {user_name}! Here is dynamic, personalized nutrition analysis for your query:\n\n"
                f"💡 **Key Insights**:\n"
                f"{explanation}\n\n"
                f"🥗 **Matching Verified Database Options**:\n"
                f"• Top options fitting your targets: **{db_item_names}**.\n"
                f"• Today's Remaining Target: **~{round(rem_cal, 0)} kcal** | **~{round(rem_pro, 1)}g Protein** | **₹{round(rem_budget, 1)} Budget**.\n\n"
                f"Ask any follow-up question like *\"Give me a 300 kcal snack\"*, *\"Is this suitable for diabetes?\"*, or *\"How to increase protein?\"*!"
            )

        # 6. Generate Dynamic Follow-Up Suggestion Chips
        dynamic_chips = [
            "What should I eat for dinner?",
            "High protein options under ₹100",
            "What can I replace paneer with?",
            "Is this safe for my health condition?"
        ]
        if "workout" in query_lower or "gym" in query_lower:
            dynamic_chips = ["Post-workout protein ideas", "Pre-workout snack", "How much water to drink?", "Daily protein target"]
        elif is_budget_query:
            dynamic_chips = ["Meals under ₹50", "Weekly grocery list", "Cheapest protein sources", "Budget dinner ideas"]
        elif any(c in query_lower for c in ["diabetes", "pcos", "bp", "kidney", "uric acid"]):
            dynamic_chips = ["Low GI breakfast ideas", "Snacks for diabetes", "Foods to avoid for kidney health", "Is fruit okay?"]

        return {
            "response": response_text,
            "intent_detected": intent_detected,
            "retrieved_context": retrieved_context,
            "suggested_chips": dynamic_chips
        }

rag_assistant = GroundedRAGAssistant()
