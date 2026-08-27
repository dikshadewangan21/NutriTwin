import os
import json
from pathlib import Path
import pandas as pd
import numpy as np

# Directory Paths
BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "datasets" / "user_profiles"
PROCESSED_DIR = BASE_DIR / "processed"

DEMO_XPT = DATASET_DIR / "demographics" / "DEMO_J.xpt"
BMX_XPT = DATASET_DIR / "examination" / "BMX_J.xpt"
DR1_XPT = DATASET_DIR / "dietary" / "DR1TOT_J.xpt"
PAQ_XPT = DATASET_DIR / "questionnaire" / "PAQ_J.xpt"

CLEANED_CSV_OUT = PROCESSED_DIR / "nhanes_user_profiles_cleaned.csv"
REPORT_JSON_OUT = PROCESSED_DIR / "nhanes_dataset_report.json"


def compute_activity_score(row: pd.Series) -> Tuple[int, str]:
    """
    Derive activity score (1-5) and string label from NHANES PAQ physical activity responses.
    """
    paq605 = row.get("PAQ605", 2.0) # Vigorous work (1=Yes, 2=No)
    paq620 = row.get("PAQ620", 2.0) # Moderate work (1=Yes, 2=No)
    paq650 = row.get("PAQ650", 2.0) # Vigorous rec (1=Yes, 2=No)
    pad680 = row.get("PAD680", 300.0) # Sedentary mins

    score = 2 # Default light activity
    if paq620 == 1.0: score += 1
    if paq605 == 1.0: score += 1
    if paq650 == 1.0: score += 1
    if pad680 >= 480.0: score -= 1

    score = max(1, min(5, score))
    act_map = {1: "sedentary", 2: "light", 3: "moderate", 4: "very_active", 5: "extra_active"}
    return score, act_map[score]


def preprocess_nhanes_dataset() -> pd.DataFrame:
    """
    Load, merge, clean, and process official NHANES 2017-2018 datasets.
    """
    print("=" * 70)
    print("[NutriTwin Phase 5] Preprocessing Official NHANES 2017-2018 Dataset...")
    print("=" * 70)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    if not DEMO_XPT.exists() or not BMX_XPT.exists() or not DR1_XPT.exists() or not PAQ_XPT.exists():
        raise FileNotFoundError(f"Missing one or more NHANES XPT files in {DATASET_DIR}")

    print("1. Loading raw NHANES SAS .xpt files...")
    demo = pd.read_sas(DEMO_XPT)
    bmx = pd.read_sas(BMX_XPT)
    dr1 = pd.read_sas(DR1_XPT)
    paq = pd.read_sas(PAQ_XPT)

    raw_total_respondents = len(demo)
    print(f"   -> Raw Respondents: Demographics={len(demo)}, Body={len(bmx)}, Dietary={len(dr1)}, Activity={len(paq)}")

    # Merge on SEQN (Respondent Sequence Number)
    merged = demo[['SEQN', 'RIDAGEYR', 'RIAGENDR']].merge(
        bmx[['SEQN', 'BMXWT', 'BMXHT', 'BMXBMI']], on='SEQN', how='inner'
    ).merge(
        dr1[['SEQN', 'DR1TKCAL', 'DR1TPROT', 'DR1TCARB', 'DR1TTFAT', 'DR1TFIBE']], on='SEQN', how='inner'
    ).merge(
        paq[['SEQN', 'PAQ605', 'PAQ620', 'PAQ650', 'PAD680']], on='SEQN', how='left'
    )

    merged_count = len(merged)
    print(f"2. Merged dataset: {merged_count} matched respondents.")

    # Filter adults (Age >= 18)
    adults = merged[merged['RIDAGEYR'] >= 18.0].copy()
    adults_count = len(adults)
    print(f"3. Adult respondents (Age >= 18): {adults_count}")

    # Handle missing values: drop rows missing core physical or calorie data
    core_cols = ['BMXBMI', 'BMXWT', 'BMXHT', 'DR1TKCAL', 'DR1TPROT', 'DR1TCARB', 'DR1TTFAT']
    cleaned = adults.dropna(subset=core_cols).copy()
    
    # Filter valid non-zero dietary intake (Calories > 400 kcal)
    cleaned = cleaned[cleaned['DR1TKCAL'] >= 400.0].copy()
    cleaned_count = len(cleaned)

    # Compute Activity Score & Gender Label
    cleaned['gender_str'] = cleaned['RIAGENDR'].apply(lambda g: "male" if g == 1.0 else "female")
    
    act_scores = []
    act_labels = []
    for idx, row in cleaned.iterrows():
        s, l = compute_activity_score(row)
        act_scores.append(s)
        act_labels.append(l)

    cleaned['activity_score'] = act_scores
    cleaned['activity_level_str'] = act_labels

    # Rename to standard NutriTwin feature names
    df_final = pd.DataFrame({
        "seqn": cleaned["SEQN"].astype(int),
        "age": cleaned["RIDAGEYR"].astype(float),
        "gender": cleaned["gender_str"],
        "weight_kg": cleaned["BMXWT"].astype(float),
        "height_cm": cleaned["BMXHT"].astype(float),
        "bmi": cleaned["BMXBMI"].astype(float),
        "daily_calories": cleaned["DR1TKCAL"].astype(float),
        "protein_g": cleaned["DR1TPROT"].astype(float),
        "carbs_g": cleaned["DR1TCARB"].astype(float),
        "fat_g": cleaned["DR1TTFAT"].astype(float),
        "fiber_g": cleaned["DR1TFIBE"].fillna(2.0).astype(float),
        "activity_score": cleaned["activity_score"].astype(int),
        "activity_level": cleaned["activity_level_str"]
    })

    # Save cleaned dataset CSV
    df_final.to_csv(CLEANED_CSV_OUT, index=False)

    report_stats = {
        "raw_total_respondents": raw_total_respondents,
        "merged_respondents": merged_count,
        "adult_respondents": adults_count,
        "cleaned_valid_profiles": cleaned_count,
        "features": list(df_final.columns),
        "output_csv": str(CLEANED_CSV_OUT)
    }

    with open(REPORT_JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(report_stats, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("NHANES DATASET PREPROCESSING SUMMARY")
    print("=" * 70)
    print(f" Merged Matched Respondents : {report_stats['merged_respondents']}")
    print(f" Adult Profiles (Age >= 18)  : {report_stats['adult_respondents']}")
    print(f" Cleaned Valid Profiles     : {report_stats['cleaned_valid_profiles']}")
    print(f" Output CSV Path            : {CLEANED_CSV_OUT}")
    print("=" * 70)

    return df_final


if __name__ == "__main__":
    preprocess_nhanes_dataset()
