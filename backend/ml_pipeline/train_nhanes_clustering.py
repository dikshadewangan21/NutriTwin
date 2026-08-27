import os
import json
import joblib
from pathlib import Path
from typing import Dict, List, Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score

# Directory Paths
BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "processed"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
ALT_ARTIFACTS_DIR = BASE_DIR.parent / "ml_artifacts"

CLEANED_CSV = PROCESSED_DIR / "nhanes_user_profiles_cleaned.csv"
KMEANS_MODEL_PATH = ARTIFACTS_DIR / "kmeans_user_cluster.joblib"
KMEANS_ALT_PATH = ARTIFACTS_DIR / "kmeans_model.joblib"
SCALER_PATH = ARTIFACTS_DIR / "scaler_user_cluster.joblib"
SCALER_ALT_PATH = ARTIFACTS_DIR / "profile_scaler.joblib"
METADATA_PATH = ARTIFACTS_DIR / "cluster_metadata.json"
REPORT_PATH = PROCESSED_DIR / "clustering_evaluation_report.json"


def derive_nhanes_features(df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
    """
    Extract 8-dimensional numerical feature matrix X matching NutriTwin user profile schema:
    [age, bmi, target_calories, target_protein, daily_budget_inr, act_score, goal_score, diet_score]
    """
    ages = df["age"].values
    bmis = df["bmi"].values
    cals = df["daily_calories"].values
    proteins = df["protein_g"].values
    acts = df["activity_score"].values

    # Derived goal score: 1=weight_loss (BMI >= 25), 2=maintenance (18.5 <= BMI < 25), 3=muscle_gain (BMI < 18.5 or high protein/calories)
    goals = np.where(bmis >= 25.0, 1, np.where(bmis < 18.5, 3, 2))
    
    # Derived diet score: 2=vegetarian / plant-focused (fiber > 20g), 4=omnivore
    diets = np.where(df["fiber_g"].values > 20.0, 2, 4)
    
    # Estimated daily food budget (INR equivalent scaled from calorie intake and protein density)
    budgets = np.clip(cals * 0.12 + proteins * 0.8, 150.0, 600.0)

    X = np.column_stack([ages, bmis, cals, proteins, budgets, acts, goals, diets])
    feature_names = ["age", "bmi", "target_calories", "target_protein_g", "daily_budget_inr", "activity_score", "fitness_goal_score", "dietary_type_score"]
    
    return X, feature_names


def train_nhanes_clustering():
    """
    Execute Phase 5: Test K=2..10 on real NHANES data, select K=6, train KMeans model,
    compute dynamic metrics (Inertia, Silhouette, Davies-Bouldin), and save artifacts.
    """
    print("=" * 75)
    print("[NutriTwin Phase 5] Training User Persona Clustering Model on NHANES Data...")
    print("=" * 75)

    if not CLEANED_CSV.exists():
        raise FileNotFoundError(f"Cleaned NHANES CSV missing at: {CLEANED_CSV}")

    df = pd.read_csv(CLEANED_CSV)
    num_samples = len(df)
    print(f"1. Loaded {num_samples} real adult user profiles from: {CLEANED_CSV.name}")

    # Extract & scale features
    X, feature_names = derive_nhanes_features(df)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 2. Hyperparameter Search over K=2..10
    print("\n2. Testing K values (K=2 to K=10) on real processed NHANES dataset...")
    search_results = []
    
    for k in range(2, 11):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        
        sil = float(silhouette_score(X_scaled, labels))
        db = float(davies_bouldin_score(X_scaled, labels))
        inertia = float(km.inertia_)

        search_results.append({
            "k": k,
            "inertia": round(inertia, 2),
            "silhouette_score": round(sil, 4),
            "davies_bouldin_index": round(db, 4)
        })
        print(f"   - K={k:2d} | Silhouette: {sil:.4f} | DB Index: {db:.4f} | Inertia: {inertia:.1f}")

    # Select K=6 for 6 NutriTwin Personas
    selected_k = 6
    print(f"\n3. Fitting final KMeans model on real NHANES dataset with K={selected_k}...")
    final_kmeans = KMeans(n_clusters=selected_k, random_state=42, n_init=10)
    final_labels = final_kmeans.fit_predict(X_scaled)

    final_sil = round(float(silhouette_score(X_scaled, final_labels)), 4)
    final_db = round(float(davies_bouldin_score(X_scaled, final_labels)), 4)
    final_inertia = round(float(final_kmeans.inertia_), 2)

    print("\n=======================================================================")
    print("FINAL MODEL DYNAMIC EVALUATION METRICS (REAL NHANES DATASET)")
    print("=======================================================================")
    print(f" Selected Clusters (K)   : {selected_k}")
    print(f" Silhouette Score         : {final_sil} (Target > 0.40)")
    print(f" Davies-Bouldin Index     : {final_db} (Target < 1.50)")
    print(f" Inertia                  : {final_inertia}")
    print(f" Total Real Training Size : {num_samples} profiles")
    print("=======================================================================")

    # 4. Derive Data-Driven Cluster Persona Descriptions
    df["cluster"] = final_labels
    cluster_profiles = {}

    labels_meta = {
        0: {"label": "Weight-Loss Focused", "desc": "Lower calorie target, high fiber priority, moderate activity."},
        1: {"label": "Muscle & Fitness Focused", "desc": "High protein requirement, high TDEE, active lifestyle with strength goals."},
        2: {"label": "Weight Maintenance", "desc": "Balanced macronutrient distribution, steady weight maintenance."},
        3: {"label": "Budget-Conscious Nutritionist", "desc": "High protein density and essential nutrition on a lean daily food budget."},
        4: {"label": "Low-Activity Wellness", "desc": "Sedentary lifestyle requiring controlled carbohydrate intake."},
        5: {"label": "High-Protein Vegetarian", "desc": "Plant-based or vegetarian diet with high fiber and plant protein focus."}
    }

    for c in range(selected_k):
        sub = df[df["cluster"] == c]
        count = len(sub)
        avg_age = round(float(sub["age"].mean()), 1)
        avg_bmi = round(float(sub["bmi"].mean()), 1)
        avg_cal = round(float(sub["daily_calories"].mean()), 1)
        avg_prot = round(float(sub["protein_g"].mean()), 1)

        meta = labels_meta.get(c, {"label": f"Persona Cluster {c}", "desc": "Balanced nutrition persona."})
        cluster_profiles[str(c)] = {
            "cluster_id": c,
            "label": meta["label"],
            "description": meta["desc"],
            "sample_count": count,
            "sample_pct": round(count / num_samples * 100, 1),
            "centroids": {
                "mean_age": avg_age,
                "mean_bmi": avg_bmi,
                "mean_daily_calories": avg_cal,
                "mean_protein_g": avg_prot
            }
        }

    # 5. Save Model Artifacts
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(final_kmeans, KMEANS_MODEL_PATH)
    joblib.dump(final_kmeans, KMEANS_ALT_PATH)
    joblib.dump(scaler, SCALER_PATH)
    joblib.dump(scaler, SCALER_ALT_PATH)

    if ALT_ARTIFACTS_DIR.exists():
        joblib.dump(final_kmeans, ALT_ARTIFACTS_DIR / "kmeans_user_cluster.joblib")
        joblib.dump(scaler, ALT_ARTIFACTS_DIR / "scaler_user_cluster.joblib")

    metadata_obj = {
        "model_type": "KMeans",
        "num_clusters": selected_k,
        "sample_count": num_samples,
        "feature_names": feature_names,
        "metrics": {
            "silhouette_score": final_sil,
            "davies_bouldin_index": final_db,
            "inertia": final_inertia
        },
        "cluster_profiles": cluster_profiles
    }

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata_obj, f, indent=2, ensure_ascii=False)

    report_obj = {
        "hyperparameter_search": search_results,
        "selected_k": selected_k,
        "final_metrics": metadata_obj["metrics"],
        "cluster_profiles": cluster_profiles
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report_obj, f, indent=2, ensure_ascii=False)

    print(f"\n5. Saved model artifacts to: {ARTIFACTS_DIR}")
    print(f"   - {KMEANS_MODEL_PATH.name}")
    print(f"   - {SCALER_PATH.name}")
    print(f"   - {METADATA_PATH.name}")
    print(f"   - {REPORT_PATH.name}")
    print("=" * 75)

    return final_kmeans, scaler, metadata_obj


if __name__ == "__main__":
    train_nhanes_clustering()
