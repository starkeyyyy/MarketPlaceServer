# models.py
from pydantic import BaseModel
from typing import List, Literal, Optional

# --- 1. Farmer Input Model ---
class FarmerInput(BaseModel):
    crop_type: str = "rice"
    soil_nitrogen: float = 40.0
    soil_phosphorus: float = 50.0
    soil_potassium: float = 30.0
    farmer_lat: float = 28.6000
    farmer_lon: float = 77.2000

# --- 2. Supplier Model ---
class Supplier(BaseModel):
    producer_name: str
    distance_km: float
    contact: str
    latitude: float
    longitude: float

# --- 3. Recommendation Response Model ---
class RecommendationResponse(BaseModel):
    crop_target: str
    soil_status: str
    deficiencies: List[Literal['N', 'P', 'K']]
    recommended_waste: str
    video_recommendation_link: str 
    location_message: str
    nearest_suppliers: List[Supplier]
    