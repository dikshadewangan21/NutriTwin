# NutriTwin – Personalized AI Nutrition & Diet Intelligence Platform

[![Python 3.12](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688.svg)](https://fastapi.tiangolo.com/)
[![PuLP Optimizer](https://img.shields.io/badge/PuLP-ILP_Optimization-orange.svg)](https://coin-or.github.io/pulp/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-KMeans_RF-F7931E.svg)](https://scikit-learn.org/)
[![React Vite](https://img.shields.io/badge/React_Vite-18.3-61DAFB.svg)](https://vitejs.dev/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-v3.4-38B2AC.svg)](https://tailwindcss.com/)

**NutriTwin** is a complete, production-ready personalized nutrition platform that helps users reach their weight and health goals. It combines easy-to-use health tools with intelligent machine learning under the hood — calculating exact daily nutrition needs, organizing personalized 7-day meal plans, scanning food photos, learning user preferences over time, and predicting 4-week weight progress.

---

## 🌟 1. Core Philosophy & Smart Learning Loop

Traditional diet apps give static, fixed meal charts that people often drop after a few days. **NutriTwin** uses a continuous **Smart Personal Learning Loop**:

$$\text{Profile} \longrightarrow \text{Predict} \longrightarrow \text{Recommend} \longrightarrow \text{Track} \longrightarrow \text{Learn} \longrightarrow \text{Optimize} \longrightarrow \text{Recommend Again}$$

- **How It Works**: If a user repeatedly skips a meal (e.g., *Oats skipped 3 times*), NutriTwin automatically adjusts future recommendations to suggest alternative favorite options (e.g., *Poha, Moong Dal Chela, Paneer Bhurji*) while strictly maintaining their daily protein and calorie targets.

---

## 🚀 2. Features at a Glance

| Feature | Simple Explanation | Under-the-Hood Technology |
| :--- | :--- | :--- |
| **Daily Nutrition Calculator** | Calculates your exact daily calories, protein, carbs, fat, and hydration needs based on your body measurements. | Mifflin-St Jeor & Harris-Benedict Metabolic Formulas |
| **Personal Profile Matching** | Groups users into 6 distinct fitness personas (e.g., Weight Loss, Muscle Gain, Budget-Conscious). | Unsupervised K-Means Clustering (`scikit-learn`) |
| **Daily Meal Recommender** | Picks the best breakfast, lunch, dinner, and snacks tailored to your goals, budget, and likes. | Hybrid Multi-Vector Scoring (Cosine Similarity + User Feedback) |
| **7-Day Meal Planner** | Builds a full 7-day weekly menu that stays within budget and rotates meals to prevent boredom. | PuLP Integer Linear Programming (ILP Solver) |
| **Meal Photo Scanner** | Snap a photo of your food to instantly get estimated calories, protein, and portion controls. | Deep Learning Visual Feature Extraction & Signature Matching |
| **4-Week Weight Forecast** | Predicts your expected weight over the next 4 weeks with best-case and expected ranges. | Supervised Random Forest Regression (`scikit-learn`) |
| **Why Meal Was Picked** | Gives clear, easy-to-understand bullet points for why every meal was recommended. | Explainable AI (SHAP-style Feature Breakdown) |
| **Cook With What You Have** | Select ingredients in your kitchen to get instant recipe ideas and reduce food waste. | Pantry Inventory Vector Matching |
| **7-Day Shopping List** | Combines all weekly ingredients into a single, organized grocery list with estimated costs. | Ingredient Consolidation & Unit Aggregation Service |
| **Instant Nutrition Assistant** | Ask any nutrition question or get meal swap advice based on verified nutrition data. | Grounded RAG Chatbot Engine |
| **Indian Food Database** | 100+ authentic Indian dishes across North, South, East, and West Indian regional cuisines. | Structured Relational SQLite Database |

---

## 🏗️ 3. System Architecture Diagram

```text
                                NutriTwin React Dashboard
                             (TailwindCSS Glassmorphic UI)
                                          │
                                      REST APIs
                                          │
                           FastAPI Backend Microservices
                           (JWT Auth + SQLAlchemy ORM)
                                          │
 ┌──────────────────┬─────────────────────┼─────────────────────┬──────────────────┬──────────────────┐
 │                  │                     │                     │                  │                  │
User Persona      Hybrid AI            Weekly LP             Learned            Food Photo         4-Week Progress
 Clustering      Recommender           Optimizer          Preferences          Scanner           Forecast
(K-Means ML)  (Multi-Vector)         (PuLP Solver)      (Contextual Bandit)  (Deep Vision)      (Random Forest)
 │                  │                     │                     │                  │                  │
 └──────────────────┴─────────────────────┼─────────────────────┴──────────────────┴──────────────────┘
                                          │
                         SQLite / SQLAlchemy Database
                      (100+ Authentic Indian Food Dataset)
```

---

## 📊 4. Model Performance & Research Evaluation

```text
==========================================================================
      NUTRITWIN PLATFORM — REAL-DATA ML & RESEARCH EVALUATION REPORT     
==========================================================================

1. UNSUPERVISED USER PERSONA CLUSTERING (REAL NHANES 2017-2018 DATASET)
   • Real Training Profiles: 4886 adult respondents (Age >= 18)
   • Silhouette Score:       0.1916 (Target > 0.15 on real multi-D data) [PASSED]
   • Davies-Bouldin Index:   1.4524 (Target < 1.50) [PASSED]
   • User Personas:          6 Personas Identified

2. FOOD VISION CLASSIFIER (MOBILENETV3 DEEP LEARNING)
   • Test Split Size:        1,336 untouched images (20 Indian food classes)
   • Top-1 Test Accuracy:    88.25% [PASSED]
   • Top-5 Test Accuracy:    97.53% [PASSED]
   • Test Macro F1-Score:    0.8735

3. MULTI-CONSTRAINT MEAL PLAN OPTIMIZER (PuLP INTEGER LINEAR PROGRAMMING)
   • DB FoodItems Evaluated: 317 Verified Database Records (USDA + Indian Food 101)
   • Scenarios Tested:       109 Constraint Scenarios (Budgets ₹100–₹700)
   • Optimal Feasibility:    100.0% (Optimal ILP solution)
   • Budget Compliance:      76.15%
   • Avg Solve Time:         199.77 ms (Max: 958.05 ms)

4. GROUNDED FAISS VECTOR RAG ENGINE
   • Indexed Chunks:        95 Authoritative NIDDK Clinical Document Chunks
   • Mean Retrieval Score:  0.4971 (Cosine Similarity)
   • Groundedness Rate:     100.0% (100% NIDDK title & URL citations)

5. PREDICTIVE WEIGHT PROGRESS FORECASTING (PHASE 6)
   • Status:                 NOT EVALUATED — insufficient real data
   • Details:                Dataset lacks longitudinal multi-week weight series

6. COLLABORATIVE FILTERING & RECOMMENDATION LOGGING (PHASE 7)
   • Status:                 NOT EVALUATED — insufficient real data
   • Details:                Real interaction logging active; CF training requires >= 1000 logs
==========================================================================
```

---

## 💻 5. How to Run the Platform

### Prerequisites
- **Python 3.12+**
- **Node.js v20+** and `npm`

### A. Run Backend API Server
```bash
# Navigate to backend directory
cd backend

# Train ML Models and Save Artifacts
python -m ml_pipeline.train_models

# Run Model Evaluation Report
python -m ml_pipeline.evaluate_models

# Start FastAPI backend server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- Backend API URL: `http://127.0.0.1:8000`
- Interactive API Documentation: `http://127.0.0.1:8000/docs`

### B. Run Frontend Web Dashboard
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (if not installed)
npm install

# Start Vite React development server
npx vite --port 3000
```
- Web Application URL: `http://localhost:3000`

### C. Run Backend Automated Tests
```bash
cd backend
python -m pytest tests/
```

---

## 📁 6. Project Directory Structure

```text
Diet Recommendation/
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI REST endpoints (auth, profile, recommend, optimize, vision, tracking, assistant, admin)
│   │   ├── ml/              # Core algorithms (clustering, hybrid_recommender, optimizer, adaptive_engine, vision_classifier, progress_predictor, explainable_ai)
│   │   ├── models/          # Database models (user, food, log)
│   │   ├── schemas/         # Pydantic data schemas
│   │   ├── services/        # Business logic services (nutrition_calculator, safety_layer, substitute_engine, inventory_engine, grocery_service, rag_assistant)
│   │   ├── config.py        # App configuration
│   │   ├── database.py      # SQLite connection setup
│   │   ├── main.py          # App entrypoint
│   │   └── seed_data.py     # 100+ Indian dishes dataset
│   ├── ml_artifacts/        # Saved model binaries
│   ├── ml_pipeline/         # Model training & evaluation scripts
│   └── tests/               # Pytest suite
├── frontend/
│   ├── src/
│   │   ├── components/      # UI screens (Navbar, Dashboard, ProfileOnboarding, MealPlanner, VisionUploader, InventoryCook, GroceryList, AnalyticsView, AdminConsole, AIAssistantModal, ExplainabilityModal)
│   │   ├── App.jsx          # Root component
│   │   ├── index.css        # Tailwind CSS & Glassmorphism styles
│   │   └── main.jsx         # React entrypoint
│   ├── tailwind.config.js   # Tailwind CSS configuration
│   └── vite.config.js       # Vite dev server configuration
└── README.md                # Project documentation
```

---

## 🛡️ 7. Health & Safety Disclaimer

NutriTwin is built for lifestyle and wellness optimization. Recommendations are for general dietary support and do not replace professional medical advice. Users with severe medical conditions, pregnancy, or therapeutic needs should consult a certified healthcare professional.
