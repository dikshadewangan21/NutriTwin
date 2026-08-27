import os
import json
import re
from pathlib import Path
from typing import Dict, List, Any

from app.database import engine, Base, SessionLocal
from app.models.food import FoodItem, SubstitutionRule
from app.seed_data import INDIAN_FOOD_DATASET, DEFAULT_SUBSTITUTION_RULES

BASE_DIR = Path(__file__).resolve().parent
CLEANED_JSON = BASE_DIR / "processed" / "indian_food_cleaned.json"


def normalize_name(name: str) -> str:
    if not name:
        return ""
    text = name.lower().strip()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip()


def import_validated_foods() -> Dict[str, int]:
    """
    Import cleaned and validated Indian Food 101 records into the SQLite database.
    Preserves existing seed data and updates/adds records safely.
    """
    print("=" * 70)
    print("[NutriTwin Phase 1] Importing Validated Foods into SQLite Database...")
    print("=" * 70)

    # 1. Ensure database tables exist
    Base.metadata.create_all(bind=engine)

    if not CLEANED_JSON.exists():
        raise FileNotFoundError(f"Cleaned dataset JSON not found at: {CLEANED_JSON}. Please run preprocess_food_dataset.py first.")

    with open(CLEANED_JSON, "r", encoding="utf-8") as f:
        cleaned_records = json.load(f)

    db = SessionLocal()
    inserted_count = 0
    updated_count = 0

    try:
        # Seed initial dataset if database is empty
        initial_count = db.query(FoodItem).count()
        if initial_count == 0:
            for item in INDIAN_FOOD_DATASET:
                food = FoodItem(**item)
                db.add(food)

            for rule in DEFAULT_SUBSTITUTION_RULES:
                sub = SubstitutionRule(**rule)
                db.add(sub)

            db.commit()
            print(f" -> Initialized seed database with {len(INDIAN_FOOD_DATASET)} items.")

        # Index existing database items by normalized name
        existing_items = db.query(FoodItem).all()
        db_name_map = {normalize_name(item.name): item for item in existing_items}

        # Import/Merge cleaned records
        for rec in cleaned_records:
            norm_name = normalize_name(rec["name"])

            if norm_name in db_name_map:
                # Update metadata fields if existing
                existing_item = db_name_map[norm_name]
                if rec.get("cuisine") and existing_item.cuisine != rec["cuisine"]:
                    existing_item.cuisine = rec["cuisine"]
                if rec.get("region") and existing_item.region != rec["region"]:
                    existing_item.region = rec["region"]
                if rec.get("ingredients") and not existing_item.ingredients:
                    existing_item.ingredients = rec["ingredients"]
                if rec.get("allergens") and not existing_item.allergens:
                    existing_item.allergens = rec["allergens"]
                updated_count += 1
            else:
                # Add new validated FoodItem record
                new_food = FoodItem(
                    name=rec["name"],
                    name_hindi=rec.get("name_hindi", ""),
                    category=rec.get("category", "snack"),
                    cuisine=rec.get("cuisine", "Pan-Indian"),
                    dietary_type=rec.get("dietary_type", "vegetarian"),
                    serving_unit=rec.get("serving_unit", "1 serving"),
                    serving_weight_g=float(rec.get("serving_weight_g", 150.0)),
                    calories=float(rec.get("calories", 0.0)),
                    protein_g=float(rec.get("protein_g", 0.0)),
                    carbs_g=float(rec.get("carbs_g", 0.0)),
                    fat_g=float(rec.get("fat_g", 0.0)),
                    fiber_g=float(rec.get("fiber_g", 0.0)),
                    approx_cost_inr=float(rec.get("approx_cost_inr", 40.0)),
                    region=rec.get("region", "All India"),
                    seasonal_months=rec.get("seasonal_months", [1,2,3,4,5,6,7,8,9,10,11,12]),
                    ingredients=rec.get("ingredients", []),
                    allergens=rec.get("allergens", []),
                    glycemic_index=rec.get("glycemic_index", "Medium"),
                    description=rec.get("description", "")
                )
                db.add(new_food)
                inserted_count += 1

        db.commit()
        final_count = db.query(FoodItem).count()

        stats = {
            "initial_db_count": initial_count,
            "imported_new_records": inserted_count,
            "updated_existing_records": updated_count,
            "final_db_count": final_count
        }

        print("\n" + "=" * 70)
        print("DATABASE IMPORT SUMMARY")
        print("=" * 70)
        print(f" Initial DB Records : {stats['initial_db_count']}")
        print(f" Imported New       : {stats['imported_new_records']}")
        print(f" Updated Existing   : {stats['updated_existing_records']}")
        print(f" Total DB Records   : {stats['final_db_count']}")
        print("=" * 70)

        return stats

    except Exception as e:
        db.rollback()
        print(f"[Import Error] Failed to import food records: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    import_validated_foods()
