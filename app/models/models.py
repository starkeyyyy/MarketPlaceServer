# models.py (Partial Update to the model handling seller input)

from typing import List, Optional # Ensure List and Optional are imported
from fastapi import UploadFile # Required if the model is used for file upload validation

class SellerOfferInput(BaseModel):
    # --- REQUIRED MANUAL FIELDS ---
    # The final price is always set manually by the seller
    cost_per_kg: float
    
    # --- OPTIONAL MANUAL / AI-FILLED FIELDS ---
    # The seller can manually input this data if the AI is skipped or fails.
    # We use Optional[T] for flexibility.
    
    # The human-defined label (e.g., "Banana Skin")
    manual_waste_type: Optional[str] = None 
    
    # The human-defined quantity (e.g., 5.0 kg)
    manual_quantity_kg: Optional[float] = None
    
    # The file input is often handled separately by FastAPI's endpoint signature, 
    # but these fields cover the manual override need.

# NOTE: The final logic will prioritize using manual_waste_type IF provided.