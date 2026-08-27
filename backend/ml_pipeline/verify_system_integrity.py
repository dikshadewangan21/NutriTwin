import os
import json
import pandas as pd
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models.user import User
from app.models.log import RecommendationInteraction
from app.ml.clustering import clustering_model
from app.ml.vision_classifier import vision_classifier
from app.ml.adaptive_engine import adaptive_engine
from app.ml.progress_predictor import progress_predictor

def run_integrity_checks():
    base_dir = Path(__file__).resolve().parent.parent.parent
    results = {}

    # 1. ML Artifacts Check
    artifacts_dir = base_dir / "backend" / "ml_pipeline" / "artifacts"
    expected_artifacts = [
        "kmeans_user_cluster.joblib",
        "scaler_user_cluster.joblib",
        "cluster_metadata.json",
        "faiss_nutrition_index",
        "mobilenet_v3_indian_food.pth",
        "vision_class_mapping.json",
        "recommender_model.joblib"
    ]
    artifacts_status = {}
    for art in expected_artifacts:
        p = artifacts_dir / art
        if p.is_dir():
            artifacts_status[art] = {"exists": True, "type": "directory"}
        else:
            artifacts_status[art] = {
                "exists": p.exists(),
                "size_bytes": p.stat().st_size if p.exists() else 0
            }
    results["ml_artifacts"] = artifacts_status

    # 2. Datasets Check
    proc_dir = base_dir / "backend" / "ml_pipeline" / "processed"
    datasets_status = {
        "indian_food_cleaned.json": (proc_dir / "indian_food_cleaned.json").exists(),
        "nhanes_user_profiles_cleaned.csv": (proc_dir / "nhanes_user_profiles_cleaned.csv").exists(),
        "user_meal_interactions.csv": (base_dir / "backend" / "ml_pipeline" / "datasets" / "interactions" / "user_meal_interactions.csv").exists(),
        "rag_chunks.json": (proc_dir / "rag" / "chunks.json").exists()
    }
    results["datasets"] = datasets_status

    # 3. API & Swagger Endpoint Startup
    client = TestClient(app)
    docs_res = client.get("/docs")
    openapi_res = client.get("/api/v1/openapi.json")
    if openapi_res.status_code != 200:
        openapi_res = client.get("/openapi.json")
    results["api_startup"] = {
        "swagger_docs_status": docs_res.status_code,
        "openapi_spec_status": openapi_res.status_code,
        "api_title": openapi_res.json().get("info", {}).get("title") if openapi_res.status_code == 200 else None
    }

    # 4. Model Loading Verification
    try:
        clustering_loaded = clustering_model.kmeans is not None
        vision_loaded = vision_classifier.model is not None
        adaptive_loaded = hasattr(adaptive_engine, "linucb") or hasattr(adaptive_engine, "update_item_weights")
        model_loading_status = {
            "clustering_model_loaded": clustering_loaded,
            "vision_classifier_loaded": vision_loaded,
            "adaptive_bandit_loaded": adaptive_loaded
        }
    except Exception as e:
        model_loading_status = {"error": str(e)}
    results["model_loading"] = model_loading_status

    # 5. Database Schema & DB Connection
    try:
        db = SessionLocal()
        user_count = db.query(User).count()
        interaction_count = db.query(RecommendationInteraction).count()
        db.close()
        db_status = {
            "valid": True,
            "users_count": user_count,
            "real_interaction_records": interaction_count
        }
    except Exception as e:
        db_status = {"valid": False, "error": str(e)}
    results["database_schema"] = db_status

    # 6. Phase 6 Progress Predictor Status Check
    test_profile = {
        "current_weight_kg": 75.0,
        "target_weight_kg": 70.0,
        "height_cm": 175.0,
        "age": 28,
        "gender": "male",
        "activity_level": "moderate",
        "fitness_goal": "weight_loss"
    }
    pred_res = progress_predictor.predict_4week_progress(test_profile)
    results["phase6_status"] = pred_res.get("status")

    # 7. Phase 7 Real Interaction Dataset Count Check
    csv_path = base_dir / "backend" / "ml_pipeline" / "datasets" / "interactions" / "user_meal_interactions.csv"
    if csv_path.exists():
        df_int = pd.read_csv(csv_path)
        csv_count = len(df_int)
    else:
        csv_count = 0
    results["phase7_interaction_counts"] = {
        "db_records": db_status.get("real_interaction_records", 0),
        "csv_records": csv_count,
        "gated_threshold_met": csv_count >= 1000
    }

    print(json.dumps(results, indent=2))
    return results

if __name__ == "__main__":
    run_integrity_checks()
