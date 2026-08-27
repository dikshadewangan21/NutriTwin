import os
import joblib
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error

BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
MODEL_FILE = ARTIFACTS_DIR / "recommender_model.joblib"

FEATURE_NAMES = [
    "macro_fit",
    "health_condition_fit",
    "preference_fit",
    "budget_fit",
    "diversity_score",
    "region_boost"
]

def train_recommendation_model(num_samples: int = 2500):
    """
    Trains a Scikit-Learn RandomForestRegressor to model the hybrid recommendation engine's
    scoring function across feature space X in R^6.
    """
    print("=" * 70)
    print("TRAINING RECOMMENDATION ML MODEL FOR SHAP EXPLAINABILITY")
    print("=" * 70)

    np.random.seed(42)

    # 1. Generate synthetic feature distribution
    macro_fit = np.random.uniform(0.0, 1.0, num_samples)
    health_fit = np.random.uniform(0.1, 1.0, num_samples)
    pref_fit = np.random.uniform(0.0, 1.0, num_samples)
    budget_fit = np.random.uniform(0.2, 1.0, num_samples)
    diversity_score = np.random.uniform(0.1, 1.0, num_samples)
    region_boost = np.random.choice([0.85, 1.0], size=num_samples, p=[0.3, 0.7])

    X = np.column_stack([
        macro_fit,
        health_fit,
        pref_fit,
        budget_fit,
        diversity_score,
        region_boost
    ])

    # Target score formula matching hybrid_recommender.py
    y = (
        0.30 * macro_fit +
        0.25 * health_fit +
        0.20 * pref_fit +
        0.10 * budget_fit +
        0.10 * diversity_score +
        0.05 * region_boost
    )

    # Add slight realistic variance (noise std < 0.005)
    noise = np.random.normal(0, 0.002, num_samples)
    y_noisy = np.clip(y + noise, 0.0, 1.0)

    # 2. Train RandomForestRegressor
    print(f"1. Training RandomForestRegressor on {num_samples} samples (6 features)...")
    rf_model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    rf_model.fit(X, y_noisy)

    # 3. Evaluate
    y_pred = rf_model.predict(X)
    r2 = r2_score(y_noisy, y_pred)
    mse = mean_squared_error(y_noisy, y_pred)

    print(f"   -> Model R^2 Score : {r2:.6f}")
    print(f"   -> Model MSE       : {mse:.8f}")

    # 4. Save Model Artifact
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(rf_model, MODEL_FILE)
    print(f"\n2. Saved trained model artifact to: {MODEL_FILE}")

    # Also save to app/ml_artifacts if exists
    alt_artifacts = BASE_DIR.parent / "ml_artifacts"
    if alt_artifacts.exists():
        joblib.dump(rf_model, alt_artifacts / "recommender_model.joblib")
        print(f"   -> Also saved to: {alt_artifacts / 'recommender_model.joblib'}")

    print("=" * 70)
    print("RECOMMENDER MODEL TRAINING COMPLETE")
    print("=" * 70)

    return rf_model, X, y_noisy

if __name__ == "__main__":
    train_recommendation_model()
