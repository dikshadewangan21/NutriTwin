import os
import csv
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from rapidfuzz import fuzz, process

# Directory Paths
BASE_DIR = Path(__file__).resolve().parent
DATASETS_DIR = BASE_DIR / "datasets"
PROCESSED_DIR = BASE_DIR / "processed"

INDIAN_FOOD_CSV = DATASETS_DIR / "indian_food" / "indian_food.csv"
USDA_FNDDS_FOOD = DATASETS_DIR / "food" / "raw" / "usda_fndds" / "food.csv"
USDA_FNDDS_NUTRIENT = DATASETS_DIR / "food" / "raw" / "usda_fndds" / "food_nutrient.csv"
USDA_NUTRIENT_NAMES = DATASETS_DIR / "food" / "raw" / "usda_fndds" / "nutrient.csv"

CLEANED_JSON_OUT = PROCESSED_DIR / "indian_food_cleaned.json"
REPORT_JSON_OUT = PROCESSED_DIR / "food_dataset_report.json"

# Try importing seed data from backend app
try:
    from app.seed_data import INDIAN_FOOD_DATASET as SEED_ITEMS
except ImportError:
    import sys
    sys.path.append(str(BASE_DIR.parent))
    from app.seed_data import INDIAN_FOOD_DATASET as SEED_ITEMS


def normalize_string(text: str) -> str:
    """Normalize string for fuzzy matching (lowercase, alphanumeric only)."""
    if not text or text == "-1":
        return ""
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip()


def parse_ingredients(ingredients_str: str) -> List[str]:
    """Parse comma-separated ingredients string into clean list."""
    if not ingredients_str or ingredients_str == "-1":
        return []
    items = [ing.strip().lower() for ing in ingredients_str.split(",")]
    return [i for i in items if i]


def detect_allergens(ingredients: List[str]) -> List[str]:
    """Detect common allergens based on ingredient list."""
    allergens = set()
    ing_text = " ".join(ingredients).lower()

    if any(k in ing_text for k in ["milk", "ghee", "paneer", "curd", "yogurt", "khoya", "khoa", "butter", "cream", "chhena"]):
        allergens.add("lactose")
    if any(k in ing_text for k in ["maida", "flour", "semolina", "rava", "wheat", "suji", "bread"]):
        allergens.add("gluten")
    if any(k in ing_text for k in ["cashews", "almonds", "pistachio", "nuts", "walnut"]):
        allergens.add("tree_nuts")
    if "peanut" in ing_text or "peanuts" in ing_text:
        allergens.add("peanuts")
    if any(k in ing_text for k in ["sesame", "til"]):
        allergens.add("sesame")
    if any(k in ing_text for k in ["mustard", "sarson"]):
        allergens.add("mustard")

    return sorted(list(allergens))


def map_course_to_category(course: str) -> str:
    """Map Indian Food 101 course to NutriTwin category (breakfast, lunch, dinner, snack)."""
    c = course.lower().strip() if course else ""
    if c == "dessert" or c == "snack" or c == "starter":
        return "snack"
    elif c == "main course":
        return "lunch" # standard main course category
    else:
        return "snack"


def map_region_to_cuisine(region: str, state: str) -> Tuple[str, str]:
    """Map Indian Food 101 region and state to NutriTwin cuisine and region."""
    r = region.strip() if region and region != "-1" else "All India"
    s = state.strip() if state and state != "-1" else ""

    if r == "North":
        cuisine = "North Indian"
    elif r == "South":
        cuisine = "South Indian"
    elif r == "West":
        cuisine = "West Indian"
    elif r == "East":
        cuisine = "East Indian"
    elif r == "North East":
        cuisine = "North East Indian"
    elif r == "Central":
        cuisine = "Central Indian"
    else:
        cuisine = "Pan-Indian"
        r = "All India"

    region_full = f"{s}, {r}" if s else r
    return cuisine, region_full


def map_dietary_type(diet: str, ingredients: List[str]) -> str:
    """Map Indian Food 101 diet to dietary_type (vegetarian, vegan, eggetarian, non_vegetarian)."""
    d = diet.lower().strip() if diet else "vegetarian"
    ing_text = " ".join(ingredients).lower()

    if "non" in d or any(k in ing_text for k in ["chicken", "mutton", "fish", "prawn", "meat"]):
        return "non_vegetarian"
    if "egg" in ing_text:
        return "eggetarian"

    # Check if vegan (no dairy/honey)
    has_dairy = any(k in ing_text for k in ["milk", "ghee", "paneer", "curd", "yogurt", "khoya", "khoa", "butter", "cream", "chhena", "condensed milk"])
    if not has_dairy:
        return "vegan"

    return "vegetarian"


def load_usda_fndds_nutrition() -> Dict[str, Dict[str, float]]:
    """
    Load USDA FNDDS survey food descriptions and their per-100g nutrient amounts.
    Returns dictionary mapping normalized USDA description to nutrient dict.
    """
    if not USDA_FNDDS_FOOD.exists() or not USDA_FNDDS_NUTRIENT.exists():
        print(f"[USDA Load] Warning: USDA dataset files not found at {USDA_FNDDS_FOOD}")
        return {}

    # In USDA FNDDS food_nutrient.csv, nutrient_id refers to nutrient_nbr (or id) in nutrient.csv
    # 208 = Energy (kcal), 203 = Protein (g), 205 = Carbohydrate (g), 204 = Total lipid (fat) (g), 291 = Fiber (g)
    nutrient_id_map = {
        "208": "calories", "1008": "calories",
        "203": "protein_g", "1003": "protein_g",
        "205": "carbs_g", "1005": "carbs_g",
        "204": "fat_g", "1004": "fat_g",
        "291": "fiber_g", "1079": "fiber_g"
    }

    if USDA_NUTRIENT_NAMES.exists():
        with open(USDA_NUTRIENT_NAMES, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                nid = row["id"]
                nnbr = row.get("nutrient_nbr", "")
                name = row["name"].lower()
                unit = row.get("unit_name", "")
                
                target_key = None
                if "energy" in name and unit == "KCAL":
                    target_key = "calories"
                elif "protein" in name and unit == "G" and "adjusted" not in name:
                    target_key = "protein_g"
                elif "carbohydrate" in name and unit == "G":
                    if "difference" in name or "summation" in name:
                        target_key = "carbs_g"
                elif "total lipid" in name and unit == "G":
                    target_key = "fat_g"
                elif "fiber, total" in name and unit == "G":
                    target_key = "fiber_g"

                if target_key:
                    if nid: nutrient_id_map[nid] = target_key
                    if nnbr: nutrient_id_map[nnbr] = target_key

    # Load FDC ID to Description map
    fdc_desc_map = {}
    with open(USDA_FNDDS_FOOD, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fdc_desc_map[row["fdc_id"]] = row["description"]

    # Load Nutrients per FDC ID
    fdc_nutrients = {}
    with open(USDA_FNDDS_NUTRIENT, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fdc_id = row["fdc_id"]
            nid = row["nutrient_id"]
            if nid in nutrient_id_map and fdc_id in fdc_desc_map:
                if fdc_id not in fdc_nutrients:
                    fdc_nutrients[fdc_id] = {
                        "calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0, "fiber_g": 0.0
                    }
                try:
                    fdc_nutrients[fdc_id][nutrient_id_map[nid]] = float(row["amount"])
                except ValueError:
                    pass

    # Map normalized description to nutrients
    usda_dict = {}
    for fdc_id, desc in fdc_desc_map.items():
        if fdc_id in fdc_nutrients:
            norm_desc = normalize_string(desc)
            if norm_desc:
                usda_dict[norm_desc] = fdc_nutrients[fdc_id]

    print(f"[USDA Load] Successfully indexed {len(usda_dict)} USDA FNDDS food descriptions.")
    return usda_dict


def match_nutrition_value(
    food_name: str,
    ingredients: List[str],
    seed_map: Dict[str, Dict[str, Any]],
    usda_dict: Dict[str, Dict[str, float]]
) -> Tuple[Dict[str, float], str, bool]:
    """
    Match food item against seed database first, then USDA FNDDS database.
    If no match, returns 0.0 macros and is_nutrition_matched = False.
    """
    norm_name = normalize_string(food_name)

    # 1. Exact match against verified Seed Data
    if norm_name in seed_map:
        seed = seed_map[norm_name]
        return {
            "serving_unit": seed.get("serving_unit", "1 portion"),
            "serving_weight_g": float(seed.get("serving_weight_g", 150.0)),
            "calories": float(seed.get("calories", 0.0)),
            "protein_g": float(seed.get("protein_g", 0.0)),
            "carbs_g": float(seed.get("carbs_g", 0.0)),
            "fat_g": float(seed.get("fat_g", 0.0)),
            "fiber_g": float(seed.get("fiber_g", 0.0)),
            "name_hindi": seed.get("name_hindi", ""),
            "approx_cost_inr": float(seed.get("approx_cost_inr", 40.0)),
            "glycemic_index": seed.get("glycemic_index", "Medium")
        }, "SEED_MATCH", True

    # 2. Token Set Fuzzy Match against Seed Data
    seed_names = list(seed_map.keys())
    match = process.extractOne(norm_name, seed_names, scorer=fuzz.token_set_ratio)
    if match and match[1] >= 75:
        matched_seed = seed_map[match[0]]
        return {
            "serving_unit": matched_seed.get("serving_unit", "1 portion"),
            "serving_weight_g": float(matched_seed.get("serving_weight_g", 150.0)),
            "calories": float(matched_seed.get("calories", 0.0)),
            "protein_g": float(matched_seed.get("protein_g", 0.0)),
            "carbs_g": float(matched_seed.get("carbs_g", 0.0)),
            "fat_g": float(matched_seed.get("fat_g", 0.0)),
            "fiber_g": float(matched_seed.get("fiber_g", 0.0)),
            "name_hindi": matched_seed.get("name_hindi", ""),
            "approx_cost_inr": float(matched_seed.get("approx_cost_inr", 40.0)),
            "glycemic_index": matched_seed.get("glycemic_index", "Medium")
        }, "SEED_FUZZY_MATCH", True

    # 3. Substring / Keyword Match against Seed Data
    for s_name, seed in seed_map.items():
        if len(norm_name) >= 4 and (norm_name in s_name or s_name in norm_name):
            return {
                "serving_unit": seed.get("serving_unit", "1 portion"),
                "serving_weight_g": float(seed.get("serving_weight_g", 150.0)),
                "calories": float(seed.get("calories", 0.0)),
                "protein_g": float(seed.get("protein_g", 0.0)),
                "carbs_g": float(seed.get("carbs_g", 0.0)),
                "fat_g": float(seed.get("fat_g", 0.0)),
                "fiber_g": float(seed.get("fiber_g", 0.0)),
                "name_hindi": seed.get("name_hindi", ""),
                "approx_cost_inr": float(seed.get("approx_cost_inr", 40.0)),
                "glycemic_index": seed.get("glycemic_index", "Medium")
            }, "SEED_SUBSTRING_MATCH", True

    # 4. Match against USDA FNDDS dataset
    if usda_dict:
        usda_names = list(usda_dict.keys())
        match_usda = process.extractOne(norm_name, usda_names, scorer=fuzz.token_set_ratio)
        if match_usda and match_usda[1] >= 72:
            usda_nutr = usda_dict[match_usda[0]]
            # Ensure USDA match has valid complete macro data
            tot_macros = usda_nutr["protein_g"] + usda_nutr["carbs_g"] + usda_nutr["fat_g"]
            if usda_nutr["calories"] <= 20 or tot_macros >= 1.0:
                portion_g = 150.0
                scale = portion_g / 100.0
                return {
                    "serving_unit": "1 portion (150g)",
                    "serving_weight_g": portion_g,
                    "calories": round(usda_nutr["calories"] * scale, 1),
                    "protein_g": round(usda_nutr["protein_g"] * scale, 1),
                    "carbs_g": round(usda_nutr["carbs_g"] * scale, 1),
                    "fat_g": round(usda_nutr["fat_g"] * scale, 1),
                    "fiber_g": round(usda_nutr["fiber_g"] * scale, 1),
                    "name_hindi": "",
                    "approx_cost_inr": 45.0,
                    "glycemic_index": "Medium"
                }, "USDA_MATCH", True

    # 5. Unmatched: Do NOT invent values (Requirement 5)
    return {
        "serving_unit": "1 serving",
        "serving_weight_g": 150.0,
        "calories": 0.0,
        "protein_g": 0.0,
        "carbs_g": 0.0,
        "fat_g": 0.0,
        "fiber_g": 0.0,
        "name_hindi": "",
        "approx_cost_inr": 35.0,
        "glycemic_index": "Medium"
    }, "UNMATCHED", False


def validate_nutrition_record(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate calories, protein, carbs, fat, fiber.
    Returns (is_valid, list_of_validation_errors).
    """
    errors = []
    cals = record.get("calories", 0.0)
    p = record.get("protein_g", 0.0)
    c = record.get("carbs_g", 0.0)
    f = record.get("fat_g", 0.0)
    fib = record.get("fiber_g", 0.0)

    # Rule 1: Non-negative
    if cals < 0 or p < 0 or c < 0 or f < 0 or fib < 0:
        errors.append("Negative nutrient value detected.")

    # Rule 2: Fiber cannot exceed carbs
    if fib > c + 0.1 and c > 0:
        errors.append(f"Fiber ({fib}g) exceeds Total Carbs ({c}g).")

    # Rule 3: Caloric consistency for matched items
    if record.get("is_nutrition_matched", False) and cals > 0:
        expected_cals = (4.0 * p) + (4.0 * c) + (9.0 * f)
        # Allow +/- 60% deviation due to fiber/rounding/water content
        if abs(cals - expected_cals) > (0.6 * max(cals, expected_cals, 50.0)):
            errors.append(f"Caloric mismatch: Reported {cals} kcal vs Atwater {round(expected_cals, 1)} kcal.")

    return len(errors) == 0, errors


def run_preprocessing_pipeline() -> Dict[str, Any]:
    """Execute complete Phase 1 preprocessing pipeline."""
    print("=" * 70)
    print("[NutriTwin Phase 1] Preprocessing Indian Food 101 & USDA Datasets...")
    print("=" * 70)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Build seed dictionary lookup
    seed_map = {normalize_string(item["name"]): item for item in SEED_ITEMS}

    # Load USDA lookup
    usda_dict = load_usda_fndds_nutrition()

    raw_records_count = 0
    duplicate_records_count = 0
    cleaned_records = []
    seen_names = set()

    matched_records_count = 0
    unmatched_records_count = 0
    invalid_records_count = 0

    # 1. Process Indian Food 101 CSV
    if not INDIAN_FOOD_CSV.exists():
        raise FileNotFoundError(f"Source Indian Food CSV missing at: {INDIAN_FOOD_CSV}")

    with open(INDIAN_FOOD_CSV, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_records_count += 1
            name = row["name"].strip()
            norm_name = normalize_string(name)

            if not norm_name:
                continue

            # Deduplication Check
            if norm_name in seen_names:
                duplicate_records_count += 1
                continue
            seen_names.add(norm_name)

            # Map text fields
            ingredients = parse_ingredients(row.get("ingredients", ""))
            allergens = detect_allergens(ingredients)
            category = map_course_to_category(row.get("course", ""))
            cuisine, region_full = map_region_to_cuisine(row.get("region", ""), row.get("state", ""))
            dietary_type = map_dietary_type(row.get("diet", ""), ingredients)

            # Nutrition Matching
            nutr_values, source_tag, is_matched = match_nutrition_value(name, ingredients, seed_map, usda_dict)
            if is_matched:
                matched_records_count += 1
            else:
                unmatched_records_count += 1

            prep_time = row.get("prep_time", "15")
            cook_time = row.get("cook_time", "20")
            flavor = row.get("flavor_profile", "")

            try:
                total_prep_mins = int(prep_time) + int(cook_time)
                if total_prep_mins <= 0: total_prep_mins = 20
            except ValueError:
                total_prep_mins = 25

            desc_parts = [f"Traditional {cuisine} dish ({row.get('course', 'delicacy')})."]
            if flavor and flavor != "-1":
                desc_parts.append(f"Flavor: {flavor.title()}.")
            if region_full and region_full != "All India":
                desc_parts.append(f"Origin: {region_full}.")
            if not is_matched:
                desc_parts.append("[UNMATCHED NUTRITION]")

            record_obj = {
                "name": name,
                "name_hindi": nutr_values["name_hindi"],
                "category": category,
                "cuisine": cuisine,
                "dietary_type": dietary_type,
                "serving_unit": nutr_values["serving_unit"],
                "serving_weight_g": nutr_values["serving_weight_g"],
                "calories": nutr_values["calories"],
                "protein_g": nutr_values["protein_g"],
                "carbs_g": nutr_values["carbs_g"],
                "fat_g": nutr_values["fat_g"],
                "fiber_g": nutr_values["fiber_g"],
                "approx_cost_inr": nutr_values["approx_cost_inr"],
                "region": region_full,
                "seasonal_months": [1,2,3,4,5,6,7,8,9,10,11,12],
                "ingredients": ingredients,
                "allergens": allergens,
                "glycemic_index": nutr_values["glycemic_index"],
                "description": " ".join(desc_parts),
                "is_nutrition_matched": is_matched,
                "nutrition_source": source_tag
            }

            # Validation Check
            is_valid, val_errors = validate_nutrition_record(record_obj)
            if not is_valid:
                invalid_records_count += 1
                record_obj["validation_errors"] = val_errors

            cleaned_records.append(record_obj)

    # 2. Save cleaned records to JSON
    with open(CLEANED_JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(cleaned_records, f, indent=2, ensure_ascii=False)

    report_stats = {
        "raw_records": raw_records_count,
        "cleaned_records": len(cleaned_records),
        "matched_records": matched_records_count,
        "unmatched_records": unmatched_records_count,
        "duplicate_records": duplicate_records_count,
        "invalid_records": invalid_records_count,
        "seed_database_items_count": len(SEED_ITEMS),
        "output_cleaned_json": str(CLEANED_JSON_OUT)
    }

    # 3. Save report artifact to JSON
    with open(REPORT_JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(report_stats, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("PHASE 1 DATA PREPROCESSING REPORT SUMMARY")
    print("=" * 70)
    print(f" Raw Records           : {report_stats['raw_records']}")
    print(f" Cleaned Records       : {report_stats['cleaned_records']}")
    print(f" Matched Records       : {report_stats['matched_records']}")
    print(f" Unmatched Records     : {report_stats['unmatched_records']}")
    print(f" Duplicate Records     : {report_stats['duplicate_records']}")
    print(f" Invalid Records       : {report_stats['invalid_records']}")
    print(f" Output JSON           : {CLEANED_JSON_OUT}")
    print("=" * 70)

    return report_stats


if __name__ == "__main__":
    run_preprocessing_pipeline()
