# recommendation.py 
import pandas as pd
from geopy.distance import geodesic
import numpy as np
from typing import List, Literal 

try:
    from app.config.api import APP_STATE 
except ImportError:
    print("Warning: APP_STATE not found. Using mock data for local testing.")
    APP_STATE = {
        'CROP_DF': pd.DataFrame({'N': [90], 'P': [45], 'K': [45], 'label': ['rice']}),
        'WASTE_MODEL': None, 
    }

CROP_DF = APP_STATE.get('CROP_DF')
WASTE_MODEL = APP_STATE.get('WASTE_MODEL')
PRODUCER_DF = APP_STATE.get('PRODUCER_DF')
OFFERS_DF = APP_STATE.get('OFFERS_DF')

DEFICIENCY_THRESHOLD = 0.6 
MAX_SEARCH_RADIUS_KM = 50 

# =======================================================
#               UTILITY FUNCTIONS
# =======================================================

def check_soil_deficiency(farmer_data, crop_target_row: pd.Series) -> List[str]:
    """Compares farmer's soil to crop target and returns list of deficiencies (N, P, K)."""
    deficiencies = []
    if farmer_data.soil_nitrogen < (crop_target_row['N'].iloc[0] * DEFICIENCY_THRESHOLD):
        deficiencies.append('N')
    if farmer_data.soil_phosphorus < (crop_target_row['P'].iloc[0] * DEFICIENCY_THRESHOLD):
        deficiencies.append('P')
    if farmer_data.soil_potassium < (crop_target_row['K'].iloc[0] * DEFICIENCY_THRESHOLD):
        deficiencies.append('K')
    return deficiencies


def find_video_link(waste_type: str, deficiency: str) -> str:
    """Generates a search link for an instructional video."""
    deficiency_str = deficiency if deficiency else "general fertility"
    search_query = f"Organic fertilizer recipe {waste_type} to fix {deficiency_str}"
    return f"https://www.youtube.com/results?search_query={'+'.join(search_query.split())}"


def find_best_offers(farmer_lat, farmer_lon, required_waste: str):
    """
    Finds available offers, joins location, calculates distance, and ranks 
    by cost (lowest first) then distance (BARGAIN MODEL).
    """
    farmer_location = (farmer_lat, farmer_lon)
    
    available_offers = OFFERS_DF[
        (OFFERS_DF['waste_type'] == required_waste) & 
        (OFFERS_DF['is_available'] == True)
    ].copy()
    
    if available_offers.empty:
        return []

    merged_df = available_offers.merge(
        PRODUCER_DF[['producer_id', 'latitude', 'longitude', 'producer_name', 'contact']], 
        on='producer_id'
    ).copy()
    
    def calculate_distance(row):
        producer_location = (row['latitude'], row['longitude'])
        return geodesic(farmer_location, producer_location).km

    merged_df['distance_km'] = merged_df.apply(calculate_distance, axis=1)
    
    final_offers = merged_df[
        merged_df['distance_km'] <= MAX_SEARCH_RADIUS_KM
    ].sort_values(by=['cost_per_kg', 'distance_km'], ascending=[True, True])
    
    return final_offers.head(5).to_dict('records')


# =======================================================
#               MAIN INTEGRATION FUNCTION
# =======================================================

def get_recommendation_data(farmer_data):
    """
    Runs the full ML prediction, deficiency check, video generation, 
    and geospatial bargain matching.
    """
    crop_target_row = CROP_DF[CROP_DF['label'] == farmer_data.crop_type.lower()]
    if crop_target_row.empty:
        raise HTTPException(status_code=404, detail=f"Crop '{farmer_data.crop_type}' not found.")

    target_npk_features_df = pd.DataFrame(
        crop_target_row[['N', 'P', 'K']].values[0].reshape(1, -1), 
        columns=['N', 'P', 'K']
    )
    predicted_class = APP_STATE['WASTE_MODEL'].predict(target_npk_features_df)[0]

    specific_waste = APP_STATE['WASTE_DF_PROCESSED'][
        APP_STATE['WASTE_DF_PROCESSED']['target_class'] == predicted_class
    ].iloc[0]

    best_waste_type = specific_waste['Waste_Type']
    
    deficiencies = check_soil_deficiency(farmer_data, crop_target_row)
    deficiency_str = ", ".join(deficiencies)
    video_link = find_video_link(best_waste_type, deficiency_str)
    
    nearest_suppliers_data = find_best_offers(
        farmer_data.farmer_lat, 
        farmer_data.farmer_lon, 
        best_waste_type
    )

    location_msg = f"Predicted Class: {predicted_class}. Ranked offers by lowest price (₹/kg)."

    return {
        "crop_target": farmer_data.crop_type,
        "soil_status": f"Soil needs boost in: {deficiency_str}",
        "deficiencies": deficiencies,
        "recommended_waste": best_waste_type,
        "video_recommendation_link": video_link, 
        "location_message": location_msg,
        "nearest_suppliers": nearest_suppliers_data # List of dictionaries
    }