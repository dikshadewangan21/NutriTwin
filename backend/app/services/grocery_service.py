class GroceryListService:
    """
    Consolidates 7-day meal plan ingredients into an aggregated grocery list
    with estimated bulk costs and store categories.
    """
    INGREDIENT_CATEGORY_MAP = {
        "rice": "Grains & Cereals",
        "basmati rice": "Grains & Cereals",
        "flattened rice": "Grains & Cereals",
        "semolina": "Grains & Cereals",
        "whole wheat flour": "Grains & Cereals",
        "sorghum flour": "Grains & Cereals",
        "millet flour": "Grains & Cereals",
        "foxtail millet": "Grains & Cereals",
        "rolled oats": "Grains & Cereals",
        
        "yellow arhar dal": "Pulses & Legumes",
        "urad dal": "Pulses & Legumes",
        "toor dal": "Pulses & Legumes",
        "yellow moong dal": "Pulses & Legumes",
        "red kidney beans": "Pulses & Legumes",
        "chana (chickpeas)": "Pulses & Legumes",
        "sprouted moong": "Pulses & Legumes",
        "textured soy protein": "Pulses & Legumes",
        
        "paneer": "Dairy & Poultry",
        "cottage cheese": "Dairy & Poultry",
        "curd": "Dairy & Poultry",
        "fresh curd": "Dairy & Poultry",
        "milk": "Dairy & Poultry",
        "butter": "Dairy & Poultry",
        "ghee": "Dairy & Poultry",
        "desi ghee": "Dairy & Poultry",
        "eggs": "Dairy & Poultry",
        "boiled eggs": "Dairy & Poultry",
        "egg whites": "Dairy & Poultry",
        "chicken breast": "Meat & Seafood",
        "rohu fish": "Meat & Seafood",
        "firm tofu": "Plant Proteins",

        "almonds": "Nuts & Dry Fruits",
        "peanuts": "Nuts & Dry Fruits",
        "cashews": "Nuts & Dry Fruits",
        "popped lotus seeds": "Nuts & Dry Fruits",

        "onion": "Vegetables & Produce",
        "tomato": "Vegetables & Produce",
        "spinach": "Vegetables & Produce",
        "cucumber": "Vegetables & Produce",
        "carrots": "Vegetables & Produce",
        "peas": "Vegetables & Produce",
        "bell peppers": "Vegetables & Produce",
        "capsicum": "Vegetables & Produce",
        "mushroom": "Vegetables & Produce",
        "okra (bhindi)": "Vegetables & Produce",
        "bottle gourd": "Vegetables & Produce",
        "banana": "Fruits",
        "apple": "Fruits",
        "papaya": "Fruits",
        "guava": "Fruits",
        "pomegranate": "Fruits"
    }

    def generate_grocery_list(self, meal_plan_items):
        """Aggregates all unique ingredients from a 7-day meal plan."""
        ingredient_counts = {}
        total_estimated_cost = 0.0

        for item in meal_plan_items:
            total_estimated_cost += item.cost_inr
            # Extract ingredients list or parse name
            ings = getattr(item, "ingredients", None)
            if not ings:
                # Basic string heuristic
                ings = [item.food_name.split()[0].lower()]

            for ing in ings:
                clean_ing = ing.strip().lower()
                if clean_ing not in ingredient_counts:
                    ingredient_counts[clean_ing] = 0
                ingredient_counts[clean_ing] += 1

        categorized_list = {}
        for ing, freq in ingredient_counts.items():
            cat = self.INGREDIENT_CATEGORY_MAP.get(ing, "Spices & Pantry Staples")
            if cat not in categorized_list:
                categorized_list[cat] = []
                
            # Estimate reasonable grocery purchase unit
            unit_str = f"{freq * 150}g" if freq < 5 else f"{round(freq * 0.2, 1)} kg"
            if "milk" in ing or "curd" in ing:
                unit_str = f"{freq * 250} ml"
            elif "egg" in ing:
                unit_str = f"{freq * 2} pcs"
            elif "banana" in ing or "apple" in ing:
                unit_str = f"{freq * 2} pcs"

            categorized_list[cat].append({
                "ingredient": ing.title(),
                "estimated_quantity": unit_str,
                "frequency_in_meals": freq
            })

        return {
            "total_estimated_cost_inr": round(total_estimated_cost, 2),
            "total_items_count": len(ingredient_counts),
            "grocery_by_category": categorized_list
        }

grocery_service = GroceryListService()
