import os
import joblib
from ml_pipeline.train_nhanes_clustering import train_nhanes_clustering
from app.ml.progress_predictor import progress_predictor
from app.config import settings

def main():
    print("[NutriTwin ML Pipeline] Executing Real ML Model Training Pipelines...")
    
    # 1. Fit K-Means User Persona Clustering Model on real NHANES dataset
    kmeans_model, scaler, metadata = train_nhanes_clustering()
    metrics = metadata["metrics"]
    print(f" -> Real NHANES K-Means Clustering Trained: Silhouette={metrics['silhouette_score']}, DB Index={metrics['davies_bouldin_index']}")
    
    # Save artifacts to app MODEL_DIR
    os.makedirs(settings.MODEL_DIR, exist_ok=True)
    joblib.dump(kmeans_model, os.path.join(settings.MODEL_DIR, "kmeans_user_cluster.joblib"))
    joblib.dump(scaler, os.path.join(settings.MODEL_DIR, "scaler_user_cluster.joblib"))
    
    # 2. Fit Random Forest Progress Predictor
    progress_predictor._fit_baseline()
    print(" -> Progress Forecasting Random Forest Model Trained.")
    joblib.dump(progress_predictor.rf_model, os.path.join(settings.MODEL_DIR, "rf_progress_predictor.joblib"))
    
    print(f"[NutriTwin ML Pipeline] Successfully saved model artifacts in {settings.MODEL_DIR}")

if __name__ == "__main__":
    main()
