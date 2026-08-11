from app.ml.clustering import clustering_model
from app.ml.adaptive_engine import adaptive_engine
from app.ml.progress_predictor import progress_predictor

def test_kmeans_clustering():
    profile = {
        "age": 28, "bmi": 24.0, "target_calories": 2200, "target_protein_g": 110,
        "daily_budget_inr": 350, "activity_level": "very_active",
        "fitness_goal": "muscle_gain", "dietary_preference": "vegetarian"
    }
    cluster_res = clustering_model.predict_cluster(profile)
    assert "cluster_id" in cluster_res
    assert "label" in cluster_res
    assert isinstance(cluster_res["cluster_id"], int)

def test_adaptive_feedback_weights():
    # Mock items
    class MockFood:
        def __init__(self, id, name):
            self.id = id
            self.name = name

    food_scores = [
        {"food": MockFood(1, "Oats Porridge"), "score": 0.9, "breakdown": {}},
        {"food": MockFood(2, "Moong Dal Chela"), "score": 0.85, "breakdown": {}}
    ]

    # Mock user skipped Oats 3 times
    class MockFeedback:
        def __init__(self, food_id, action_type):
            self.food_id = food_id
            self.action_type = action_type
            self.rating = None

    logs = [MockFeedback(1, "skipped"), MockFeedback(1, "skipped"), MockFeedback(1, "skipped")]
    updated = adaptive_engine.update_item_weights(food_scores, logs)
    
    # Moong Dal Chela should now be ranked #1 above Oats
    assert updated[0]["food"].id == 2
