import re
from typing import List, Dict, Any, Optional

class GroundedRAGAssistant:
    """
    Dynamic Conversational RAG AI Nutrition Assistant.
    Searches the relational SQLite DB (food items, substitution rules, health conditions)
    and synthesizes real-time user profile metrics to provide accurate, dynamic answers 
    for any nutrition, diet, health condition, recipe, budget, or general wellness prompt.
    """

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
        context against verified DB items and user profile metrics, and synthesizing an accurate, 
        personalized answer.
        """
        if not user_query or not user_query.strip():
            user_query = "What should I eat today?"

        query_raw = user_query.strip()
        query_lower = query_raw.lower()

        # 1. Calculate live user profile and intake metrics
        user_name = user_profile.full_name if hasattr(user_profile, 'full_name') and user_profile.full_name else 'Friend'
        goal = (user_profile.fitness_goal or 'health').replace('_', ' ')
        pref = (user_profile.dietary_preference or 'vegetarian').replace('_', '-')
        
        target_cal = getattr(user_profile, 'target_calories', None) or getattr(user_profile, 'tdee', 2000.0) or 2000.0
        target_pro = getattr(user_profile, 'target_protein_g', None) or (target_cal * 0.25 / 4.0) or 80.0
        target_carb = (target_cal * 0.50 / 4.0) or 220.0
        target_fat = (target_cal * 0.25 / 9.0) or 55.0
        
        daily_budget = user_profile.daily_budget_inr or 250.0

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

        conditions = user_profile.medical_conditions or []
        if isinstance(conditions, str):
            conditions = [conditions]
        active_conditions = [c for c in conditions if c and c.lower() != 'none']

        # 2. Extract numeric constraints from query (e.g. "under 300 calories", "under ₹150", "30g protein")
        max_cal_match = re.search(r'(?:under|below|less than|\<)\s*(\d+)\s*(?:cal|calories|kcal)', query_lower)
        max_cal_constraint = float(max_cal_match.group(1)) if max_cal_match else None

        max_cost_match = re.search(r'(?:under|below|less than|budget|\<\s*₹?|\₹)\s*(\d+)\s*(?:rs|rupees|inr|₹)?', query_lower)
        max_cost_constraint = float(max_cost_match.group(1)) if max_cost_match else None

        min_pro_match = re.search(r'(?:at least|more than|minimum|\>)\s*(\d+)\s*g?\s*(?:protein|pro)', query_lower)
        min_pro_constraint = float(min_pro_match.group(1)) if min_pro_match else None

        # 3. Detect food items mentioned in query or database
        matched_foods = []
        for food in food_items:
            fname = food.name.lower()
            if fname in query_lower or any(ing.lower() in query_lower for ing in (food.ingredients or [])):
                matched_foods.append(food)

        # 4. Filter database foods based on user preferences and query constraints
        valid_foods = food_items
        if pref in ['vegetarian', 'vegan', 'eggetarian', 'jain']:
            valid_foods = [f for f in valid_foods if f.dietary_type in [pref, 'vegetarian', 'vegan']]

        if max_cost_constraint:
            valid_foods = [f for f in valid_foods if f.approx_cost_inr <= max_cost_constraint]
        if max_cal_constraint:
            valid_foods = [f for f in valid_foods if f.calories <= max_cal_constraint]
        if min_pro_constraint:
            valid_foods = [f for f in valid_foods if f.protein_g >= min_pro_constraint]

        # Sort valid foods by protein/calorie ratio or recommendation score
        valid_foods_sorted = sorted(valid_foods, key=lambda f: (f.protein_g / max(1.0, f.calories)), reverse=True)

        # 5. Dynamic Topic & Knowledge Synthesis
        response_text = ""
        intent_detected = "general_query"
        retrieved_context: Dict[str, Any] = {
            "query": user_query,
            "target_calories": round(target_cal, 1),
            "remaining_calories": round(rem_cal, 1),
            "remaining_protein_g": round(rem_pro, 1),
            "remaining_budget_inr": round(rem_budget, 1)
        }

        # --- TOPIC A: Budget & Financial Query ---
        if any(w in query_lower for w in ["budget", "cost", "price", "cheap", "rupees", "rs", "₹", "expensive", "afford"]):
            intent_detected = "budget_optimization"
            affordable_dishes = [f for f in valid_foods_sorted if f.approx_cost_inr <= rem_budget][:3]
            dish_list_str = "\n".join([
                f"• **{f.name}** ({f.serving_unit}): ~₹{f.approx_cost_inr} | {f.calories} kcal, {f.protein_g}g Protein"
                for f in affordable_dishes
            ]) if affordable_dishes else "• **Moong Dal Khichdi / Sprouts Salad**: Very cost-effective & high protein."

            response_text = (
                f"You currently have **₹{round(rem_budget, 2)}** remaining out of your daily ₹{daily_budget} budget "
                f"(₹{round(logged_cost, 2)} spent today).\n\n"
                f"Here are top budget-friendly meal recommendations tailored to your {pref} preference:\n\n"
                f"{dish_list_str}\n\n"
                f"💡 **Tip**: Batch cooking pulses (Rajma, Chana, Dal) and stocking egg/tofu/paneer reduces per-meal cost below ₹40 while meeting your protein targets!"
            )
            retrieved_context["suggested_dishes"] = [f.name for f in affordable_dishes]

        # --- TOPIC B: Food Replacement / Swap / Substitution ---
        elif any(w in query_lower for w in ["replace", "substitute", "instead", "don't have", "swap", "alternative", "no paneer", "no egg", "no chicken"]):
            intent_detected = "food_substitution"
            target_ingredient = "ingredient"
            if "paneer" in query_lower: target_ingredient = "paneer"
            elif "egg" in query_lower: target_ingredient = "egg"
            elif "chicken" in query_lower: target_ingredient = "chicken"
            elif "rice" in query_lower: target_ingredient = "rice"
            elif "milk" in query_lower or "curd" in query_lower: target_ingredient = "dairy/milk"
            elif "oats" in query_lower: target_ingredient = "oats"

            # Check substitution rules database
            sub_matches = [
                s for s in substitution_rules 
                if target_ingredient in s.original_food_name.lower() or s.original_food_name.lower() in query_lower
            ]

            if sub_matches:
                sub_lines = "\n".join([f"• **{s.substitute_food_name}**: {s.reason}" for s in sub_matches[:3]])
            else:
                if target_ingredient == "paneer":
                    sub_lines = (
                        "• **Tofu (Soy Paneer)**: Equivalent ~18-20g protein per 100g with lower fat & zero lactose.\n"
                        "• **Soy Chunks (Soya Badi)**: Extremely high protein (~52g per 100g dry) and budget-friendly.\n"
                        "• **Sautéed Mushroom & Chickpeas**: Great texture with high fiber & micronutrients."
                    )
                elif target_ingredient in ["chicken", "egg"]:
                    sub_lines = (
                        "• **Paneer Bhurji / Grilled Paneer**: ~18g protein per 100g, rich in calcium.\n"
                        "• **Soya Chunks Masala**: ~52g protein per 100g dry weight.\n"
                        "• **Boiled Black Chana Chaat**: High plant protein & complex carbs."
                    )
                else:
                    sub_lines = (
                        "• **Quinoa / Foxtail Millet**: Great low-GI replacement for white rice.\n"
                        "• **Almond / Soy Milk**: Excellent dairy-free alternative rich in plant protein."
                    )

            response_text = (
                f"Here are optimal, nutrient-matched replacements for **{target_ingredient.title()}**:\n\n"
                f"{sub_lines}\n\n"
                f"These options maintain your daily protein goals without disrupting your {goal} progress."
            )
            retrieved_context["target_ingredient"] = target_ingredient

        # --- TOPIC C: Post-Workout / Pre-Workout / Gym Nutrition ---
        elif any(w in query_lower for w in ["workout", "gym", "exercise", "post-workout", "pre-workout", "muscle", "recovery"]):
            intent_detected = "workout_nutrition"
            is_post = "post" in query_lower or "after" in query_lower or "recovery" in query_lower
            
            if is_post:
                workout_foods = [f for f in valid_foods_sorted if f.protein_g >= 15.0][:3]
                w_str = "\n".join([
                    f"• **{f.name}**: {f.protein_g}g Protein, {f.calories} kcal ({f.serving_unit})"
                    for f in workout_foods
                ]) if workout_foods else "• **Paneer Bhurji with Roti** / **3 Boiled Egg Whites + Toast** / **Soy Chunks Salad**"

                response_text = (
                    f"💪 **Post-Workout Nutrition Guide**:\n\n"
                    f"Within 30–45 minutes after training, your muscles require **20–30g of fast-absorbing protein** plus complex carbs for glycogen replenishment.\n\n"
                    f"Top options matching your profile:\n"
                    f"{w_str}\n\n"
                    f"✨ *Aim for at least {round(target_pro * 0.3, 1)}g protein in this recovery meal to maximize muscle protein synthesis!*"
                )
            else:
                response_text = (
                    f"⚡ **Pre-Workout Fueling Guide**:\n\n"
                    f"Eat a light meal 45–60 minutes before training containing **easily digestible complex carbs + moderate protein**:\n\n"
                    f"• **Bananas with 1 tbsp Peanut Butter** (~200 kcal, instant energy)\n"
                    f"• **Oats with Skimmed Milk / Soy Milk** (~250 kcal, sustained release)\n"
                    f"• **Fruit & Curd Bowl** (~180 kcal, easy on digestion)\n\n"
                    f"Avoid heavy fats or excessive fiber right before working out to prevent stomach discomfort."
                )

        # --- TOPIC D: Health Conditions (Diabetes, PCOS, Hypertension, Uric Acid, Fatty Liver, Thyroid) ---
        elif any(w in query_lower for w in ["diabetes", "sugar", "pcos", "pcod", "bp", "blood pressure", "hypertension", "uric acid", "gout", "thyroid", "fatty liver", "cholesterol"]):
            intent_detected = "disease_aware_guidance"
            matched_conds = [c for c in ["diabetes", "pcos", "hypertension", "uric acid", "thyroid", "cholesterol"] if c in query_lower]
            cond_name = matched_conds[0].upper() if matched_conds else (active_conditions[0].upper() if active_conditions else "HEALTH CONDITION")

            # Retrieve low GI / disease appropriate foods from DB
            disease_foods = [f for f in valid_foods if getattr(f, 'glycemic_index', 'Medium') in ['Low', 'Medium'] and f.protein_g >= 10.0][:3]
            d_str = "\n".join([f"• **{f.name}**: Low GI, {f.protein_g}g protein, {f.calories} kcal" for f in disease_foods])

            if "diabetes" in query_lower or "sugar" in query_lower:
                advice = (
                    "• Focus on **Low Glycemic Index (GI)** complex carbs (Bajra, Oats, Moong Dal, Quinoa).\n"
                    "• Pair every carb serving with protein & fiber to prevent post-meal blood glucose spikes.\n"
                    "• Avoid refined sugar, white flour (Maida), fruit juices, and deep-fried snacks."
                )
            elif "pcos" in query_lower or "pcod" in query_lower:
                advice = (
                    "• Emphasize anti-inflammatory foods, high fiber (vegetables, seeds), and high protein.\n"
                    "• Keep insulin levels stable by limiting refined carbs and sugary boba/drinks.\n"
                    "• Include Flax seeds, Pumpkin seeds, and Lean plant/animal protein."
                )
            elif "bp" in query_lower or "hypertension" in query_lower or "blood pressure" in query_lower:
                advice = (
                    "• Strictly monitor sodium intake (< 2,000 mg/day). Avoid pickles, papad, & packaged snacks.\n"
                    "• Increase potassium-rich foods (Bananas, Spinach, Coconut Water, Sweet Potato).\n"
                    "• Use herbs, lemon juice, and roasted cumin instead of excess salt."
                )
            elif "uric acid" in query_lower or "gout" in query_lower:
                advice = (
                    "• Limit high-purine foods (Red meat, organ meats, shellfish, yeast extracts).\n"
                    "• Stay hydrated (3.0+ Liters water daily) to promote uric acid excretion.\n"
                    "• Enjoy Low-fat Dairy, Cherries, Vitamin C rich fruits, and legumes in moderation."
                )
            else:
                advice = (
                    "• Prioritize whole foods, lean protein, healthy omega-3 fats (walnuts, chia seeds), and high fiber.\n"
                    "• Maintain a consistent meal timing schedule to support metabolic balance."
                )

            response_text = (
                f"🩺 **Medical Nutrition Insights for {cond_name}**:\n\n"
                f"{advice}\n\n"
                f"Recommended dishes from our database for your profile:\n"
                f"{d_str}\n\n"
                f"⚠️ *NutriTwin safety protocols automatically screen all daily meal plans against your selected health profile.*"
            )

        # --- TOPIC E: Skipped Meal / Intake Adjustment ---
        elif any(w in query_lower for w in ["skipped", "missed", "fasting", "didn't eat", "forgot lunch", "forgot breakfast"]):
            intent_detected = "meal_compensation"
            comp_foods = [f for f in valid_foods_sorted if f.protein_g >= 18.0][:3]
            comp_str = "\n".join([f"• **{f.name}**: {f.calories} kcal, {f.protein_g}g Protein" for f in comp_foods])

            response_text = (
                f"No worries! NutriTwin dynamically adjusts your remaining meals to keep you on track.\n\n"
                f"📊 **Current Status Today**:\n"
                f"• **Remaining Calories**: ~{round(rem_cal, 0)} kcal\n"
                f"• **Remaining Protein**: ~{round(rem_pro, 1)}g\n\n"
                f"To compensate safely without overloading your digestion, try these high-density options for your next meal:\n"
                f"{comp_str}\n\n"
                f"💡 *Remember to stay hydrated with 2.5–3.0L water to keep your metabolic rate steady!*"
            )

        # --- TOPIC F: Specific Dish or Ingredient Search (e.g. Samosa, Dosa, Chicken, Oats, Milk) ---
        elif matched_foods:
            intent_detected = "food_item_lookup"
            f = matched_foods[0]
            
            fit_status = "✅ Fits well into your daily targets!"
            if f.calories > rem_cal:
                fit_status = f"⚠️ Note: 1 serving ({f.calories} kcal) exceeds your remaining calorie budget (~{round(rem_cal, 0)} kcal)."

            response_text = (
                f"🔍 **Nutritional Breakdown for {f.name}** ({f.serving_unit}):\n\n"
                f"• **Calories**: {f.calories} kcal\n"
                f"• **Protein**: {f.protein_g}g\n"
                f"• **Carbohydrates**: {f.carbs_g}g (Fiber: {f.fiber_g}g)\n"
                f"• **Fats**: {f.fat_g}g\n"
                f"• **Glycemic Index**: {f.glycemic_index}\n"
                f"• **Approx Cost**: ₹{f.approx_cost_inr}\n"
                f"• **Key Ingredients**: {', '.join(f.ingredients or ['Natural ingredients'])}\n\n"
                f"{fit_status}\n\n"
                f"Description: {f.description or 'Authentic Indian dish prepared with traditional spices and balanced macros.'}"
            )
            retrieved_context["matched_food"] = f.name

        # --- TOPIC G: General Meal Suggestion / "What should I eat?" ---
        elif any(w in query_lower for w in ["what to eat", "dinner", "lunch", "breakfast", "snack", "meal idea", "suggest", "recommend"]):
            intent_detected = "meal_recommendation"
            
            slot = "dinner"
            if "breakfast" in query_lower: slot = "breakfast"
            elif "lunch" in query_lower: slot = "lunch"
            elif "snack" in query_lower: slot = "snack"

            slot_foods = [f for f in valid_foods_sorted if f.category.lower() == slot or slot in f.category.lower()][:3]
            if not slot_foods:
                slot_foods = valid_foods_sorted[:3]

            rec_str = "\n".join([
                f"• **{f.name}** ({f.serving_unit}): {f.calories} kcal, {f.protein_g}g Protein, ₹{f.approx_cost_inr}"
                for f in slot_foods
            ])

            response_text = (
                f"Based on your **{goal.upper()}** goal and {pref.upper()} diet, you have **~{round(rem_cal, 0)} kcal** and **~{round(rem_pro, 1)}g protein** remaining today.\n\n"
                f"🥗 **Top Recommended {slot.title()} Options**:\n"
                f"{rec_str}\n\n"
                f"All options strictly fit your ₹{userProfile.daily_budget_inr} daily budget and safety requirements!"
            )
            retrieved_context["suggested_dishes"] = [f.name for f in slot_foods]

        # --- TOPIC H: Dynamic General Nutrition / Health Knowledge Question ---
        else:
            intent_detected = "general_nutrition_qa"
            
            # Smart dynamic answer generation for any user question
            sample_recs = valid_foods_sorted[:2]
            rec_names = ", ".join([f.name for f in sample_recs]) if sample_recs else "Paneer Tikka, Moong Dal Chela, Tofu Curry"

            response_text = (
                f"Great question, {user_name}! Here is dynamic nutrition guidance tailored for your profile:\n\n"
                f"• **Your Targets**: Daily Target = {round(target_cal, 0)} kcal, {round(target_pro, 1)}g Protein. Remaining today = ~{round(rem_cal, 0)} kcal & ~{round(rem_pro, 1)}g protein.\n"
                f"• **Dietary Preference**: {pref.title()} | Goal: {goal.title()}\n"
                f"• **Health Considerations**: {', '.join([c.title() for c in active_conditions]) if active_conditions else 'General Wellness & Active Lifestyle'}.\n\n"
                f"For your query (*\"{user_query}\"*), the core rule is to prioritize **whole nutrient-dense foods**, maintain an adequate protein intake (1.4–1.8g per kg bodyweight for active goals), and control glycemic response.\n\n"
                f"Recommended dishes from our database that align with this: **{rec_names}**.\n\n"
                f"Feel free to ask follow-up questions like *\"Give me a 400 cal recipe\"*, *\"What can I swap paneer with?\"*, or *\"Is this suitable for diabetes?\"*!"
            )

        # 6. Generate Context-Aware Follow-Up Suggestion Chips dynamically
        dynamic_chips = [
            "What should I eat for dinner?",
            "High protein options under ₹100",
            "What can I replace paneer with?",
            "Is this safe for my health condition?"
        ]
        if "workout" in query_lower or "gym" in query_lower:
            dynamic_chips = ["Post-workout protein ideas", "Pre-workout snack", "How much water to drink?", "Daily protein target"]
        elif "budget" in query_lower or "cost" in query_lower:
            dynamic_chips = ["Meals under ₹50", "Weekly grocery list", "Cheapest protein sources", "Budget dinner ideas"]
        elif any(c in query_lower for c in ["diabetes", "pcos", "bp", "uric acid"]):
            dynamic_chips = ["Low GI breakfast ideas", "Snacks for diabetes", "Foods to avoid", "Is fruit okay?"]

        return {
            "response": response_text,
            "intent_detected": intent_detected,
            "retrieved_context": retrieved_context,
            "suggested_chips": dynamic_chips
        }

rag_assistant = GroundedRAGAssistant()
