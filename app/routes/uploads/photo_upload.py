# routes/uploads/photo_upload.py
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from pydantic import BaseModel
from typing import Dict, Any, Optional
from io import BytesIO
import google as genai # Needed for the client initialization
import json # Needed to parse the JSON response from Gemini
from PIL import Image

# --- IMPORTS for Services and Global State ---
from app.services.waste_calculator import calculate_weighted_npk_score, calculate_manual_npk_score
from app.services.marketplace_services import save_offer_to_marketplace
from app.config.state import APP_STATE 

# --- Define the Input Schemas ---
# (SellerManualInput class remains the same)
class SellerManualInput(BaseModel):
    manual_waste_type: Optional[str] = None 
    manual_quantity_kg: Optional[float] = None
    cost_per_kg: float 
    producer_id: str 
    
# --- Define the Expected Output Schema (MUST match what you send to Gemini) ---
# NOTE: This is replicated here for context but should live in models.py
DETECTION_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "label": {"type": "string", "description": "The exact waste item name."},
            "relative_quantity_score": {"type": "number", "description": "Score from 1 to 10."}
        },
        "required": ["label", "relative_quantity_score"]
    }
}

router = APIRouter(
    prefix="/upload",
    tags=["Supplier Uploads"]
)

# --- Define the Image Processing Endpoint ---
@router.post("/photo", summary="Uploads image, processes NPK via Gemini, and saves offer.")
async def upload_waste_photo(
    file: Optional[UploadFile] = File(None),
    cost_per_kg: float = Form(...),
    producer_id: str = Form(...),
    manual_waste_type: Optional[str] = Form(None),
    manual_quantity_kg: Optional[float] = Form(None),
) -> Dict[str, Any]:
    
    # 1. INITIAL SETUP
    offer_data = SellerManualInput(
        cost_per_kg=cost_per_kg,
        producer_id=producer_id,
        manual_waste_type=manual_waste_type,
        manual_quantity_kg=manual_quantity_kg
    )
    is_image_mode = (file is not None)
    final_npk_scores = {}
    final_waste_type = None
    final_quantity = 0.0
    source_message = ""
    
    if not is_image_mode and (offer_data.manual_waste_type is None or offer_data.manual_quantity_kg is None):
        raise HTTPException(status_code=400, detail="Missing Data: Must upload an image OR provide manual details.")

    # --- 2. EXECUTE LOGIC (AI vs. Manual) ---

    if is_image_mode:
        # **A. AI/VISION MODE (Gemini is Executed Here)**
        try:
            image_bytes = await file.read()
            image_pil = Image.open(BytesIO(image_bytes))

            # --- CRITICAL GEMINI API CALL ---
            client = APP_STATE['GEMINI_CLIENT'] # Client loaded from global state
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[image_pil, "Identify ALL distinct organic waste items and estimate their relative quantity score (1-10)."],
                config={
                    "response_mime_type": "application/json",
                    "response_schema": DETECTION_SCHEMA,
                    "temperature": 0.1
                }
            )
            # --- END API CALL ---

            # Parse the structured JSON response
            detection_results = json.loads(response.text)
            
            # Use the service function to calculate the weighted NPK score
            npk_calc_result = calculate_weighted_npk_score(
                detection_results=detection_results,
                waste_npk_df=APP_STATE['WASTE_DF_PROCESSED']
            )

            if npk_calc_result.get("status") == "success":
                final_waste_type = npk_calc_result['dominant_waste_type']
                final_npk_scores = npk_calc_result['combined_npk_score']
                final_quantity = npk_calc_result['total_area_proxy'] 
                source_message = "Data sourced via Gemini Vision Analysis."
            else:
                is_image_mode = False # Fallback if classification fails

        except Exception as e:
            print(f"WARNING: Image/Gemini processing failed: {e}")
            is_image_mode = False # Fallback if any error occurs
    
    
    # **B. MANUAL MODE (Fallback or Direct Input)**
    if not is_image_mode and offer_data.manual_waste_type and offer_data.manual_quantity_kg:
        final_waste_type = offer_data.manual_waste_type
        final_quantity = offer_data.manual_quantity_kg
        
        final_npk_scores = calculate_manual_npk_score(
            final_waste_type, 
            final_quantity, 
            APP_STATE['WASTE_DF_PROCESSED']
        )
        source_message = "Data provided manually by seller."
    
    # Final check for data completeness
    if not final_waste_type:
        raise HTTPException(status_code=400, detail="Cannot process offer. Image analysis failed, and required manual fields are missing.")

    # --- 3. SAVE THE FINAL OFFER TO THE MARKETPLACE ---
    try:
        # Call the persistence service
        offer_id = save_offer_to_marketplace(
            producer_id=offer_data.producer_id,
            cost_per_kg=offer_data.cost_per_kg,
            waste_type=final_waste_type,
            estimated_quantity=final_quantity,
            npk_scores=final_npk_scores,
            offers_df=APP_STATE['OFFERS_DF']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database persistence failed on save: {e}")

    # --- 4. RETURN FINAL ANALYSIS INTERFACE ---
    return {
        "status": "ANALYSIS_SUCCESSFUL",
        "listing_id": offer_id, 
        "seller_input_source": source_message,
        "final_analysis": {
            "waste_type": final_waste_type,
            "calculated_npk_score": final_npk_scores,
            "estimated_quantity_proxy": round(final_quantity, 2),
            "seller_price_per_kg": offer_data.cost_per_kg,
        }
    }