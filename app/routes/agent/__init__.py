routes/agent/__init__.py 

from fastapi import APIRouter, Depends
from models import FarmerInput, RecommendationResponse
from .recommendation import get_recommendation_data 

router = APIRouter(tags=["Agent/Recommendation"])

@router.post("/recommend\_fertilizer", response_model=RecommendationResponse)
def post_recommendation(farmer_data: FarmerInput):
    """Endpoint for fertilizer and bargain recommendation."""
    return get_recommendation_data(farmer_data)