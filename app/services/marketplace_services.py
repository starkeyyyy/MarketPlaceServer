# app/services/marketplace_service.py (Final Save Logic)

import pandas as pd
import uuid
from datetime import datetime
from app.config.api import APP_STATE # Required for global access

def save_offer_to_marketplace(
    producer_id: str,
    cost_per_kg: float,
    waste_type: str,
    estimated_quantity: float,
    npk_scores: Dict[str, float],
) -> str: # Returns the new offer ID
    """
    Saves the final calculated offer details to the OFFERS_DF and the CSV file.
    """
    
    # Generate unique ID and structure the data
    new_offer_id = f"O-{uuid.uuid4().hex[:8].upper()}"
    new_data = {
        'offer_id': new_offer_id,
        'producer_id': producer_id,
        'waste_type': waste_type,
        'quantity_kg': estimated_quantity,
        'cost_per_kg': cost_per_kg,
        'is_available': True,
        'listing_date': datetime.now().isoformat(),
        'N_score': npk_scores['N'],
        'P_score': npk_scores['P'],
        'K_score': npk_scores['K'],
    }
    
    # 1. APPEND TO GLOBAL DATAFRAME (Makes data available to live API requests instantly)
    # Convert the new data to a DataFrame row
    new_row_df = pd.DataFrame([new_data])
    
    # Use pd.concat to update the global OFFERS_DF object in memory
    # NOTE: This requires APP_STATE['OFFERS_DF'] to be a mutable object (a DataFrame).
    # Since DataFrames are generally mutable, this works in a prototype environment.
    APP_STATE['OFFERS_DF'] = pd.concat([APP_STATE['OFFERS_DF'], new_row_df], ignore_index=True)
    
    # 2. PERSISTENCE: Write back to CSV (Ensures data survives server restart)
    APP_STATE['OFFERS_DF'].to_csv(APP_STATE['DATA_PATH'] / 'offers.csv', index=False)
    
    return new_offer_id