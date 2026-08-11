import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score

CLUSTER_PROFILES = {
    0: {
        "label": "Weight-Loss Focused",
        "description": "Lower calorie intake target, high dietary fiber focus, moderate protein requirement.",
        "key_traits": ["Calorie Deficit Target", "High Fiber Priority", "Moderate Activity"]
    },
    1: {
        "label": "Muscle & Fitness Focused",
        "description": "High protein requirement, high TDEE, active lifestyle with strength goals.",
        "key_traits": ["High Protein (>1.8g/kg)", "Calorie Surplus/Maintenance", "Highly Active"]
    },
    2: {
        "label": "Weight Maintenance",
        "description": "Balanced macronutrient distribution, moderate activity, steady weight maintenance.",
        "key_traits": ["Balanced Macros", "Moderate Budget", "Steady Maintenance"]
    },
    3: {
        "label": "Budget-Conscious Nutritionist",
        "description": "Prioritizes high protein and essential nutrition on a lean daily food budget.",
        "key_traits": ["Strict Budget (<= ₹250/day)", "High Protein Density", "Cost Optimization"]
    },
    4: {
        "label": "Low-Activity Wellness",
        "description": "Sedentary lifestyle requiring controlled carbohydrate intake and dense micronutrients.",
        "key_traits": ["Sedentary/Desk Job", "Controlled Carbs", "Low Calorie TDEE"]
    },
    5: {
        "label": "High-Protein Vegetarian",
        "description": "Plant-based or vegetarian diet requiring optimized plant protein sources (paneer, soy, lentils).",
        "key_traits": ["Vegetarian/Vegan", "Plant Protein Priority", "Nutritional Substitution Needed"]
    }
}

class UserClusteringModel:
    def __init__(self, n_clusters=6):
        self.n_clusters = n_clusters
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        self.is_fitted = False

    def _extract_features(self, profile_dict):
        """Extract numerical feature vector from user profile dictionary."""
        age = profile_dict.get("age", 25)
        bmi = profile_dict.get("bmi", 22.5)
        target_calories = profile_dict.get("target_calories", 2000.0)
        target_protein = profile_dict.get("target_protein_g", 70.0)
        daily_budget = profile_dict.get("daily_budget_inr", 300.0)
        
        act_map = {"sedentary": 1, "light": 2, "moderate": 3, "very_active": 4, "extra_active": 5}
        act_score = act_map.get(profile_dict.get("activity_level", "moderate"), 3)
        
        goal_map = {"weight_loss": 1, "maintenance": 2, "muscle_gain": 3, "health": 2}
        goal_score = goal_map.get(profile_dict.get("fitness_goal", "maintenance"), 2)
        
        diet_map = {"vegan": 1, "vegetarian": 2, "eggetarian": 3, "non_vegetarian": 4}
        diet_score = diet_map.get(profile_dict.get("dietary_preference", "vegetarian"), 2)
        
        return np.array([age, bmi, target_calories, target_protein, daily_budget, act_score, goal_score, diet_score])

    def fit_synthetic_dataset(self, num_samples=300):
        """Fit clustering model on representative user population data."""
        np.random.seed(42)
        ages = np.random.randint(18, 65, num_samples)
        bmis = np.random.uniform(18.5, 34.0, num_samples)
        cals = np.random.uniform(1400, 3200, num_samples)
        proteins = np.random.uniform(45, 160, num_samples)
        budgets = np.random.uniform(150, 600, num_samples)
        acts = np.random.randint(1, 6, num_samples)
        goals = np.random.randint(1, 4, num_samples)
        diets = np.random.randint(1, 5, num_samples)
        
        X = np.column_stack([ages, bmis, cals, proteins, budgets, acts, goals, diets])
        X_scaled = self.scaler.fit_transform(X)
        self.kmeans.fit(X_scaled)
        self.is_fitted = True
        
        labels = self.kmeans.labels_
        sil_score = float(silhouette_score(X_scaled, labels))
        db_index = float(davies_bouldin_score(X_scaled, labels))
        
        return {
            "silhouette_score": round(sil_score, 4),
            "davies_bouldin_index": round(db_index, 4),
            "num_clusters": self.n_clusters,
            "sample_count": num_samples
        }

    def predict_cluster(self, profile_dict):
        """Predict cluster assignment and return cluster traits."""
        if not self.is_fitted:
            self.fit_synthetic_dataset()
            
        feat = self._extract_features(profile_dict).reshape(1, -1)
        feat_scaled = self.scaler.transform(feat)
        cluster_id = int(self.kmeans.predict(feat_scaled)[0])
        
        meta = CLUSTER_PROFILES.get(cluster_id, {
            "label": "Custom Persona",
            "description": "Balanced diet persona tailored to unique user parameters.",
            "key_traits": ["Custom Fitness Plan"]
        })
        
        return {
            "cluster_id": cluster_id,
            "label": meta["label"],
            "description": meta["description"],
            "key_traits": meta["key_traits"]
        }

clustering_model = UserClusteringModel()
