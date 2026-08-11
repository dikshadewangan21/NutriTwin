from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.food import FoodItem
from app.api.auth import get_current_user
from app.ml.vision_classifier import vision_classifier

router = APIRouter(prefix="/vision", tags=["Food Scanner & Vision Recognition"])


@router.post("/scan-meal")
async def scan_meal_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze a meal photo using multi-signal computer vision (color histograms,
    texture analysis, RGB ratios) and return top matching Indian foods with
    nutrition data from the database.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Please upload an image file (JPEG, PNG, or WEBP)."
        )

    contents = await file.read()

    # Limit file size to 10MB
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="Image is too large. Please upload a photo under 10MB."
        )

    all_foods = db.query(FoodItem).all()
    result = vision_classifier.process_image(contents, all_foods)
    return result


@router.get("/food-search")
def search_food_by_name(
    q: str = Query(..., min_length=2, description="Partial food name to search"),
    limit: int = Query(5, ge=1, le=15),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fuzzy search the food database by name (supports partial names, Hindi names,
    spelling variations). Used for manual override after scan.
    """
    all_foods = db.query(FoodItem).all()
    matches = vision_classifier.fuzzy_search(q, all_foods, limit=limit)
    return {
        "query": q,
        "results_count": len(matches),
        "results": matches
    }
