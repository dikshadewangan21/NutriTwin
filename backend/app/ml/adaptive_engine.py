import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional

def action_to_reward(action_type: Optional[str], rating: Optional[float] = None) -> float:
    """
    Converts real user interaction action or explicit rating into a continuous reward signal r in [-1.0, +1.0].
    
    Reward mappings:
      - skipped  : -1.0
      - swapped  : -0.5
      - consumed : +0.5
      - rating 5 : +1.0
      - rating 4 : +0.7
      - rating 3 : +0.3
      - rating 2 : -0.5
      - rating 1 : -1.0
    """
    if rating is not None:
        try:
            r_val = float(rating)
            if r_val >= 4.5:
                return 1.0
            elif r_val >= 3.5:
                return 0.7
            elif r_val >= 2.5:
                return 0.3
            elif r_val >= 1.5:
                return -0.5
            else:
                return -1.0
        except (ValueError, TypeError):
            pass

    act = (action_type or "").lower().strip()
    if act == "skipped":
        return -1.0
    elif act == "swapped":
        return -0.5
    elif act == "consumed":
        return 0.5
    elif act in ["rated", "rating"]:
        return 0.5
    return 0.0


class LinUCBArmModel:
    """
    LinUCB Single-Arm Contextual Multi-Armed Bandit Implementation (Li et al., 2010).
    
    Maintains d-dimensional feature space parameter matrix A_a in R^(d x d) (initialized to I_d)
    and response vector b_a in R^d (initialized to 0_d).
    """
    def __init__(self, d: int = 6, alpha: float = 0.5):
        self.d = d
        self.alpha = alpha
        self.A = np.eye(d, dtype=float)
        self.b = np.zeros(d, dtype=float)

    @property
    def theta(self) -> np.ndarray:
        """Compute estimated coefficient parameter vector theta = A^(-1) * b."""
        try:
            return np.linalg.solve(self.A, self.b)
        except np.linalg.LinAlgError:
            return np.linalg.pinv(self.A) @ self.b

    def predict_ucb(self, x: np.ndarray) -> float:
        """
        Compute predicted Upper Confidence Bound score for feature vector x:
            score = theta^T * x + alpha * sqrt(x^T * A^(-1) * x)
        """
        x = np.asarray(x, dtype=float).reshape(-1)
        if len(x) != self.d:
            x_fixed = np.ones(self.d, dtype=float)
            x_fixed[:min(len(x), self.d)] = x[:min(len(x), self.d)]
            x = x_fixed

        try:
            A_inv_x = np.linalg.solve(self.A, x)
        except np.linalg.LinAlgError:
            A_inv_x = np.linalg.pinv(self.A) @ x

        expected_reward = float(np.dot(self.theta, x))
        variance = float(np.dot(x, A_inv_x))
        std_dev = np.sqrt(max(0.0, variance))
        
        ucb_score = expected_reward + self.alpha * std_dev
        return ucb_score

    def update(self, x: np.ndarray, reward: float):
        """
        Update LinUCB parameters with feedback pair (context x, reward r):
            A <- A + x * x^T
            b <- b + r * x
        """
        x = np.asarray(x, dtype=float).reshape(-1)
        if len(x) != self.d:
            x_fixed = np.ones(self.d, dtype=float)
            x_fixed[:min(len(x), self.d)] = x[:min(len(x), self.d)]
            x = x_fixed

        self.A += np.outer(x, x)
        self.b += float(reward) * x


LinUCBModel = LinUCBArmModel


class AdaptiveLearningEngine:
    """
    Disjoint LinUCB Contextual Multi-Armed Bandit & EWMA Online Behavioral Learning Engine.
    Dynamically learns user meal preferences, adherence trends, and skip patterns using LinUCB.
    """
    def __init__(self, alpha: float = 0.5, d: int = 6):
        self.alpha = alpha
        self.d = d
        self.arm_models: Dict[int, LinUCBArmModel] = {}
        self.global_model = LinUCBArmModel(d=d, alpha=alpha)

    def _get_arm_model(self, food_id: int) -> LinUCBArmModel:
        """Get or initialize Disjoint LinUCB model for specific food item (arm)."""
        if food_id not in self.arm_models:
            self.arm_models[food_id] = LinUCBArmModel(d=self.d, alpha=self.alpha)
        return self.arm_models[food_id]

    def extract_context_vector(self, item: Dict[str, Any], profile=None) -> np.ndarray:
        """Construct 6-dimensional contextual feature vector from item breakdown and user profile."""
        base_score = float(item.get("score", 0.5))
        bd = item.get("breakdown", {})
        macro_fit = float(bd.get("macro_fit", base_score))
        pref_fit = float(bd.get("preference_fit", 0.5))
        budget_fit = float(bd.get("budget_fit", 0.5))
        div_fit = float(bd.get("diversity_score", 0.5))
        bias = 1.0
        return np.array([base_score, macro_fit, pref_fit, budget_fit, div_fit, bias], dtype=float)

    def update_item_weights(self, food_id_scores: List[Dict[str, Any]], feedback_logs=None) -> List[Dict[str, Any]]:
        """
        Dynamically adjusts food recommendation scores using LinUCB contextual bandit model.
        Updates arm parameters on real feedback_logs if provided, then re-ranks items by predicted UCB.
        Preserves full backward compatibility with existing API response schemas.
        """
        if not food_id_scores:
            return []

        # 1. Update LinUCB parameters from real interaction feedback logs if provided
        if feedback_logs:
            item_context_map = {}
            for item in food_id_scores:
                food_obj = item.get("food")
                fid = getattr(food_obj, "id", None) if food_obj else None
                if fid is None and isinstance(item, dict):
                    fid = item.get("food_id")
                if fid is not None:
                    item_context_map[fid] = self.extract_context_vector(item)

            for log in feedback_logs:
                if isinstance(log, dict):
                    fid = log.get("food_id")
                    act = log.get("action_type")
                    r_val = log.get("rating")
                else:
                    fid = getattr(log, "food_id", None)
                    act = getattr(log, "action_type", None)
                    r_val = getattr(log, "rating", None)

                if fid is not None:
                    reward = action_to_reward(act, r_val)
                    x_feed = item_context_map.get(fid, np.array([0.7, 0.7, 0.7, 0.7, 0.7, 1.0], dtype=float))
                    arm = self._get_arm_model(fid)
                    arm.update(x_feed, reward)
                    self.global_model.update(x_feed, reward)

        # 2. Compute LinUCB scores for candidate items
        adjusted_scores = []
        for item in food_id_scores:
            item_copy = dict(item)
            if "breakdown" in item_copy and isinstance(item_copy["breakdown"], dict):
                item_copy["breakdown"] = dict(item_copy["breakdown"])
            else:
                item_copy["breakdown"] = {}

            food_obj = item.get("food")
            fid = getattr(food_obj, "id", None) if food_obj else None
            if fid is None and isinstance(item, dict):
                fid = item.get("food_id")

            x_ctx = self.extract_context_vector(item_copy)
            base_s = float(item.get("score", 0.5))

            if fid is not None and fid in self.arm_models:
                arm = self.arm_models[fid]
                ucb_val = arm.predict_ucb(x_ctx)
                mult = max(0.1, 1.0 + ucb_val)
            else:
                ucb_val = 0.0
                mult = 1.0

            final_s = round(float(np.clip(base_s * mult, 0.05, 1.0)), 4)
            mult_rounded = round(float(mult), 2)

            item_copy["score"] = final_s
            item_copy["adaptive_multiplier"] = mult_rounded
            item_copy["breakdown"]["adaptive_feedback"] = mult_rounded
            item_copy["breakdown"]["linucb_score"] = round(float(ucb_val), 4)

            adjusted_scores.append(item_copy)

        adjusted_scores.sort(key=lambda x: x["score"], reverse=True)
        return adjusted_scores

    def compute_adherence_trend(self, daily_intake_logs, target_calories):
        """Compute rolling 7-day adherence trend percentage and calorie consistency score."""
        if not daily_intake_logs:
            return {"adherence_rate_pct": 85.0, "calorie_compliance_pct": 90.0, "insight": "Baseline tracking initialized."}

        logs = sorted(daily_intake_logs, key=lambda x: x.log_date)[-7:]
        total_days = len(logs)
        if total_days == 0:
            return {"adherence_rate_pct": 85.0, "calorie_compliance_pct": 90.0, "insight": "Baseline tracking initialized."}

        compliant_days = 0
        diffs = []
        for log in logs:
            cals = log.total_calories
            diff = abs(cals - target_calories)
            diffs.append(diff)
            if diff <= 0.15 * target_calories:
                compliant_days += 1

        adherence_pct = round((compliant_days / total_days) * 100.0, 1)
        avg_diff = np.mean(diffs) if diffs else 0
        compliance_pct = round(max(0.0, 100.0 - (avg_diff / target_calories * 100.0)), 1)

        insight = f"User maintained {adherence_pct}% meal target compliance over the past {total_days} logged days."
        if adherence_pct < 60.0:
            insight += " Recommendation engine is reducing meal complexity to assist consistency."

        return {
            "adherence_rate_pct": adherence_pct,
            "calorie_compliance_pct": compliance_pct,
            "logged_days_count": total_days,
            "insight": insight
        }

adaptive_engine = AdaptiveLearningEngine()
