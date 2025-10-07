import google as genai
import json
from PIL import Image
from io import BytesIO
import os 
# 1. Define the Expected Output Schema (using a Python dictionary)
DETECTION_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "label": {"type": "string", "description": "The exact waste item name (e.g., 'Banana Skin')."},
            "relative_quantity_score": {"type": "number", "description": "Estimate the item's quantity as a score from 1 to 10 (10 being very large)."}
        },
        "required": ["label", "relative_quantity_score"]
    }
}

def call_gemini_vision_api(image_bytes: bytes, client: genai.Client) -> List[Dict]:
    """Sends image and detailed prompt for structured detection and quantity estimation."""
    
    # 2. Prepare Multimodal Content
    image = Image.open(BytesIO(image_bytes))
    
    # SYSTEM PROMPT: Forces the model to use strict rules
    system_instruction = (
        "You are a waste assessment expert. Analyze all organic waste items. "
        "Your response MUST be a JSON array of objects that strictly adheres to the provided schema. "
        "DO NOT include any text outside the JSON block."
    )
    
    user_prompt = (
        "Identify ALL distinct organic waste items. For each item, provide a 'relative_quantity_score' "
        "from 1 (very small/trace) to 10 (very large/dominant)."
    )

    # 3. Call the API with Structured Output Config
    response = client.models.generate_content(
        model='gemini-2.5-flash', # Fastest multimodal model
        contents=[image, user_prompt],
        config={
            "response_mime_type": "application/json",
            "response_schema": DETECTION_SCHEMA,
            "system_instruction": system_instruction,
            "temperature": 0.1 # Low temperature for reliable data extraction
        }
    )
    
    # 4. Parse the result and prepare it for the NPK calculation
    # The output is a JSON string, which must be loaded back into a Python list/dict
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        print("ERROR: Gemini did not return valid JSON.")
        return []