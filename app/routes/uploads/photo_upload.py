# routes/uploads/photo_upload.py

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from io import BytesIO

# --- IMPORTANT IMPORTS (Assumed available in the project structure) ---
from app.services.waste_calculator import calculate_weighted_npk_score 
from app.config.api import APP_STATE 

# --- Define the Input Schema for Form Data ---
# This model handles the manual inputs the seller provides alongside the file.
class SellerManualInput(BaseModel):
    # This field is OPTIONAL if an image is provided, required otherwise
    manual_waste_type: Optional[str] = None 
    
    # This field is OPTIONAL if an image is provided, required otherwise
    manual_quantity_kg: Optional[float] = None
    
    # The price is always required and set manually by the seller
    cost_per_kg: float 
    
    # Static data for location lookup (assumed to be associated with the seller's account)
    producer_id: str 
    
    # Note: We must also handle the 'file' parameter in the endpoint function signature itself.


router = APIRouter(
    prefix="/upload",
    tags=["Supplier Uploads"]
)

# --- Define the Image Processing Router ---

@router.post("/photo", summary="Uploads waste image, calculates NPK score, and prepares offer data.")
async def upload_waste_photo(
    # FastAPI handles the file upload
    file: Optional[UploadFile] = File(None),
    # Get form fields and validate them using the Pydantic model
    cost_per_kg: float = Form(...),
    producer_id: str = Form(...),
    manual_waste_type: Optional[str] = Form(None),
    manual_quantity_kg: Optional[float] = Form(None),
) -> Dict[str, Any]:
    
    # Combine form data into a Pydantic object for clean processing
    offer_data = SellerManualInput(
        cost_per_kg=cost_per_kg,
        producer_id=producer_id,
        manual_waste_type=manual_waste_type,
        manual_quantity_kg=manual_quantity_kg
    )

    # --- 1. DETERMINE INPUT PATH (AI vs. MANUAL) ---
    is_image_mode = (file is not None)
    
    # Check for critical missing data: must have EITHER image OR full manual details
    if not is_image_mode and (offer_data.manual_waste_type is None or offer_data.manual_quantity_kg is None):
        raise HTTPException(
            status_code=400,
            detail="Missing Data: Must upload an image OR provide both manual_waste_type and manual_quantity_kg."
        )

    # --- 2. EXECUTE LOGIC ---

    if is_image_mode:
        # **A. AI/VISION MODE (Prioritized)**
        try:
            image_bytes = await file.read()
            
            # --- This is the key call to the multimodal AI ---
            # NOTE: Assuming analyze_waste_with_gemini is imported or defined elsewhere 
            # and returns the calculated NPK score and dominant waste type based on the image.
            
            # Placeholder Call (Replace with actual Gemini function call)
            # This call uses the internal NPK DataFrame for context
            npk_calculation_result = analyze_waste_with_gemini(
                image_bytes=image_bytes,
                waste_npk_df=APP_STATE['WASTE_DF_PROCESSED'] 
            )

        except Exception as e:
            # If the AI fails, check if manual override is available
            if offer_data.manual_waste_type and offer_data.manual_quantity_kg:
                print("WARNING: AI failed, falling back to manual input.")
                is_image_mode = False # Switch to manual logic below
            else:
                raise HTTPException(status_code=503, detail=f"Image processing failed and no manual fallback provided: {e}")
    
    
    # **B. MANUAL MODE (Fallback or Direct Input)**
    if not is_image_mode:
        # Use the explicit manual inputs for the final offer creation
        final_waste_type = offer_data.manual_waste_type
        final_quantity = offer_data.manual_quantity_kg
        
        # Calculate NPK score based on single manual item (simplified service call)
        # NOTE: This uses a simplified service based on single item concentration * quantity
        # This function would need to be defined to handle single item calculation.
        final_npk_scores = calculate_manual_npk_score(final_waste_type, final_quantity, APP_STATE['WASTE_DF_PROCESSED'])
        
        source_message = "Data provided manually by seller."

    else:
        # Use the successful AI result
        final_waste_type = npk_calculation_result['dominant_waste_type']
        final_npk_scores = npk_calculation_result['combined_npk_score']
        final_quantity = npk_calculation_result['total_area_proxy'] # Use area proxy as final quantity
        source_message = "Data sourced via Gemini Vision Analysis."
    
    
    # --- 3. PREPARE FINAL MARKET OFFER ---
    
    # In a real system, you would insert this data into the offers.csv/database
    
    return {
        "status": "Offer Data Generated",
        "listing_id": "NEW_OFFER_123",
        "seller_input_source": source_message,
        "final_offer_details": {
            "waste_type": final_waste_type,
            "calculated_npk_score": final_npk_scores,
            "estimated_quantity": round(final_quantity, 2),
            "seller_price_per_kg": offer_data.cost_per_kg,
            "producer_id": offer_data.producer_id,
        }
    }