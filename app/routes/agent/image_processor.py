# image_processor.py

from ultralytics import YOLO
import numpy as np
from fastapi import UploadFile
from typing import List
import io 
from PIL import Image 

MODEL_WEIGHTS_PATH = '/Users/varun/Desktop/ML code/MarketPlaceServer/app/yolo_model/best.pt' 

CLASSES = ['Apple', 'Apple-core', 'Apple-peel', 'Banana', 'Bone', 'Bone-fish', 'Bread', 'Bun', 'Chicken-skin', 'Congee', 'Cucumber', 'Drink', 'Egg-hard', 'Egg-scramble', 'Egg-shell', 'Egg-steam', 'Egg-yolk', 'Fish', 'Meat', 'Mushroom', 'Mussel', 'Mussel-shell', 'Noodle', 'Orange', 'Orange-peel', 'Other-waste', 'Pancake', 'Pasta', 'Pear', 'Pear-core', 'Pear-peel', 'Potato', 'Rice', 'Shrimp', 'Shrimp-shell', 'Tofu', 'Tomato', 'Vegetable', 'Vegetable-root']


try:
    INFERENCE_MODEL = YOLO(MODEL_WEIGHTS_PATH)
    print(f"✅ YOLOv8 Model loaded from: {MODEL_WEIGHTS_PATH}")
except Exception as e:
    INFERENCE_MODEL = None
    print(f"CRITICAL ERROR: Failed to load YOLO model: {e}")

# =================================================================
# FUNCTION: Classify the Uploaded Image
# =================================================================

def classify_waste_image(file: UploadFile) -> str:
    """
    Reads the uploaded image file, runs YOLOv8 inference, and returns 
    the predicted class label.
    """
    if INFERENCE_MODEL is None:
        return "Model_Not_Loaded_Error"

    try:
        # Read the file content into a memory buffer
        image_bytes = file.file.read()
        
        # Use PIL to open the image from bytes (YOLO prefers PIL or numpy formats)
        image = Image.open(io.BytesIO(image_bytes))

        # Run inference (YOLO handles all preprocessing/resizing internally)
        results = INFERENCE_MODEL.predict(
            source=image, 
            conf=0.25,      # Minimum confidence score
            iou=0.45,       # Intersection over Union threshold
            verbose=False   # Keep terminal output clean
        )
        
        # --- Post-Processing: Extract the Best Prediction ---
        
        if not results or not results[0].boxes:
            return "No_Object_Detected"
        
        # Get the detection with the highest confidence
        best_box = results[0].boxes[0]
        
        # Get the class ID (as an integer)
        class_id = int(best_box.cls.cpu().numpy()[0])
        
        # Map the ID back to the class name
        predicted_label = CLASSES[class_id]
        
        return predicted_label

    except Exception as e:
        print(f"Inference run failed: {e}")
        return "Prediction_Failed"