import pandas as pd
from typing import List, Dict, Any

# --- NOTE: This function requires APP_STATE['WASTE_DF_PROCESSED'] to be accessible globally.
# It is assumed that the calling router (photo_upload.py) will pass this DataFrame.

def get_npk_row(waste_label: str, waste_npk_df: pd.DataFrame) -> pd.Series | None:
    """Safely retrieves the NPK concentration row for a given waste label."""
    npk_row = waste_npk_df[waste_npk_df['Waste_Type'] == waste_label]
    if npk_row.empty:
        return None
    # Return the first matching row as a Series object
    return npk_row.iloc[0]

def calculate_manual_npk_score(
    waste_label: str, 
    quantity_kg: float, 
    waste_npk_df: pd.DataFrame
) -> Dict[str, float]:
    """
    Calculates the NPK score for a SINGLE, manually confirmed waste item.
    This is used for the manual input fallback path.
    """
    
    npk_row = get_npk_row(waste_label, waste_npk_df)
    
    if npk_row is None:
        # Raise error if the manually entered item is not in the database
        raise ValueError(f"Waste type '{waste_label}' not found in NPK database.")
        
    # Get NPK concentration (from N_mg, P_mg, K_mg columns)
    n_conc = npk_row['Nitrogen_mg']
    p_conc = npk_row['Phosphorus_mg']
    k_conc = npk_row['Potassium_mg']
    
    # Calculate Weighted NPK (Concentration * Absolute Mass)
    final_npk = {
        'N': n_conc * quantity_kg,
        'P': p_conc * quantity_kg,
        'K': k_conc * quantity_kg
    }

    return final_npk


def calculate_weighted_npk_score(
    detection_results: List[Dict[str, Any]], 
    waste_npk_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Calculates the combined NPK concentration and total quantity proxy for a batch 
    of detected waste items (used in AI/Vision mode).
    """
    total_npk = {'N': 0.0, 'P': 0.0, 'K': 0.0}
    total_area_proxy = 0.0
    item_area_contributions = {}
    
    # 1. Iterate through all detected objects (from Gemini/YOLO)
    for item in detection_results:
        label = item['label']
        
        # Quantity Proxy: Use the relative score (from Gemini) or the box dimensions (from YOLO)
        # We assume the input provides box_w and box_h (0-1 normalized) or a score.
        box_w = item.get('box_w', 0.0) 
        box_h = item.get('box_h', 0.0)
        
        area = box_w * box_h # This is the quantity weight for the weighted average
        if area <= 0: continue
            
        total_area_proxy += area
        
        # 2. Lookup NPK concentration
        npk_row = get_npk_row(label, waste_npk_df)
        if npk_row is None:
            continue
            
        # Get NPK concentration (from N_mg, P_mg, K_mg columns)
        n_conc = npk_row['Nitrogen_mg']
        p_conc = npk_row['Phosphorus_mg']
        k_conc = npk_row['Potassium_mg']
        
        # 3. Calculate Weighted NPK (Concentration * Area) and accumulate
        total_npk['N'] += n_conc * area
        total_npk['P'] += p_conc * area
        total_npk['K'] += k_conc * area
        
        item_area_contributions[label] = item_area_contributions.get(label, 0) + area

    # 4. Final Dominant Waste Type and Result Aggregation
    if not item_area_contributions:
        return {"status": "failed", "message": "No recognized organic waste detected."}

    dominant_waste = max(item_area_contributions, key=item_area_contributions.get)

    return {
        "status": "success",
        "dominant_waste_type": dominant_waste,
        "combined_npk_score": total_npk,
        "total_area_proxy": total_area_proxy,
    }
