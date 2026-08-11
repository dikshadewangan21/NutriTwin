class PantryInventoryEngine:
    """
    Leftover & Pantry Cooking Engine generating high-protein recipes using ingredients
    currently available in user's kitchen to minimize food waste.
    """
    def find_pantry_recipes(self, pantry_ingredients, food_db_items, user_profile):
        """Matches available ingredients against Indian food database dishes."""
        pantry_set = set([ing.strip().lower() for ing in pantry_ingredients])
        if not pantry_set:
            return []

        matched_recipes = []
        user_allergies = set([a.lower() for a in (user_profile.allergies or [])])
        user_diet = user_profile.dietary_preference or "vegetarian"

        for food in food_db_items:
            # Check safety & allergies
            food_allergens = set([a.lower() for a in (food.allergens or [])])
            if user_allergies.intersection(food_allergens):
                continue
            if user_diet == "vegan" and food.dietary_type != "vegan":
                continue
            elif user_diet == "vegetarian" and food.dietary_type not in ["vegetarian", "vegan"]:
                continue

            food_ings = set([i.strip().lower() for i in (food.ingredients or [])])
            if not food_ings:
                continue

            # Calculate intersection of ingredients
            matched_ings = food_ings.intersection(pantry_set)
            missing_ings = food_ings.difference(pantry_set)
            
            match_pct = (len(matched_ings) / float(len(food_ings))) * 100.0

            if len(matched_ings) > 0:
                matched_recipes.append({
                    "food": food,
                    "match_pct": round(match_pct, 1),
                    "matched_ingredients": list(matched_ings),
                    "missing_ingredients": list(missing_ings),
                    "can_cook_immediately": len(missing_ings) == 0
                })

        matched_recipes.sort(key=lambda x: (x["match_pct"], x["food"].protein_g), reverse=True)
        return matched_recipes

inventory_engine = PantryInventoryEngine()
