import os
import json
from pathlib import Path
import pandas as pd
from datetime import datetime

from app.database import SessionLocal, engine, Base
from app.models.log import RecommendationInteraction

# Directory Paths
BASE_DIR = Path(__file__).resolve().parent
INTERACTIONS_DIR = BASE_DIR / "datasets" / "interactions"
PROCESSED_DIR = BASE_DIR / "processed"

CSV_OUT_PATH = INTERACTIONS_DIR / "user_meal_interactions.csv"
REPORT_OUT_PATH = PROCESSED_DIR / "interaction_export_report.json"


def export_user_meal_interactions() -> pd.DataFrame:
    """
    Export logged real user meal recommendation interactions from database
    to CSV dataset at ml_pipeline/datasets/interactions/user_meal_interactions.csv.
    Does NOT generate any fake synthetic user interaction data.
    """
    print("=" * 70)
    print("[NutriTwin Phase 7] Exporting Real User Recommendation Interactions...")
    print("=" * 70)

    INTERACTIONS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Ensure tables are created in SQLite
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        query = db.query(RecommendationInteraction).order_by(RecommendationInteraction.id.asc())
        records = query.all()
        
        rows = []
        for r in records:
            rows.append({
                "interaction_id": r.id,
                "user_id": r.user_id,
                "food_id": r.food_id,
                "timestamp": r.timestamp.isoformat() if r.timestamp else datetime.utcnow().isoformat(),
                "shown": int(r.shown),
                "clicked": int(r.clicked),
                "consumed": int(r.consumed),
                "skipped": int(r.skipped),
                "swapped": int(r.swapped),
                "rating": r.rating if r.rating is not None else "",
                "context_json": json.dumps(r.context or {})
            })

        df = pd.DataFrame(rows, columns=[
            "interaction_id", "user_id", "food_id", "timestamp",
            "shown", "clicked", "consumed", "skipped", "swapped", "rating", "context_json"
        ])

        df.to_csv(CSV_OUT_PATH, index=False)

        total_records = len(df)
        total_shown = int(df["shown"].sum()) if total_records > 0 else 0
        total_clicked = int(df["clicked"].sum()) if total_records > 0 else 0
        total_consumed = int(df["consumed"].sum()) if total_records > 0 else 0
        total_skipped = int(df["skipped"].sum()) if total_records > 0 else 0
        total_swapped = int(df["swapped"].sum()) if total_records > 0 else 0

        report = {
            "exported_at": datetime.utcnow().isoformat(),
            "output_csv": str(CSV_OUT_PATH),
            "total_logged_interactions": total_records,
            "interaction_counts": {
                "shown": total_shown,
                "clicked": total_clicked,
                "consumed": total_consumed,
                "skipped": total_skipped,
                "swapped": total_swapped
            },
            "sufficient_data_for_collaborative_filtering": bool(total_records >= 1000 and total_consumed >= 200),
            "recommendation": "Collaborative filtering model training requires >= 1000 real interactions with >= 200 consumed/rated items."
        }

        with open(REPORT_OUT_PATH, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f" Output CSV Path            : {CSV_OUT_PATH}")
        print(f" Total Logged Interactions  : {total_records}")
        print(f" Shown: {total_shown} | Clicked: {total_clicked} | Consumed: {total_consumed} | Skipped: {total_skipped} | Swapped: {total_swapped}")
        print(f" Collaborative Filtering    : {'READY' if report['sufficient_data_for_collaborative_filtering'] else 'HEURISTIC (Awaiting real user interaction volume)'}")
        print("=" * 70)

        return df
    finally:
        db.close()


if __name__ == "__main__":
    export_user_meal_interactions()
