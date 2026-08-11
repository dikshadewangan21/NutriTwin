import os
import joblib
from app.ml.clustering import clustering_model
from app.ml.progress_predictor import progress_predictor
from app.config import settings

def main():
    print("[NutriTwin ML Pipeline] Training ML Models...")
    
    # 1. Fit K-Means User Clustering Model
    cluster_metrics = clustering_model.fit_synthetic_dataset(num_samples=500)
    print(f" -> K-Means Clustering Trained: Silhouette={cluster_metrics['silhouette_score']}, DB Index={cluster_metrics['davies_bouldin_index']}")
    
    # Save artifacts
    os.makedirs(settings.MODEL_DIR, exist_ok=True)
    joblib.dump(clustering_model.kmeans, os.path.join(settings.MODEL_DIR, "kmeans_user_cluster.joblib"))
    joblib.dump(clustering_model.scaler, os.path.join(settings.MODEL_DIR, "scaler_user_cluster.joblib"))
    
    # 2. Fit Random Forest Progress Predictor
    progress_predictor._fit_baseline()
    print(" -> Progress Forecasting Random Forest Model Trained.")
    joblib.dump(progress_predictor.rf_model, os.path.join(settings.MODEL_DIR, "rf_progress_predictor.joblib"))
    
    print(f"[NutriTwin ML Pipeline] Successfully saved model artifacts in {settings.MODEL_DIR}")

if __name__ == "__main__":
    main()
