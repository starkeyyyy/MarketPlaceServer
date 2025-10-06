# app/config/api.py 
import joblib
import pandas as pd
from fastapi import FastAPI
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent 
DATA_PATH = '/Users/varun/Desktop/ML code/MarketPlaceServer/app/data/'
MODEL_PATH = '/Users/varun/Desktop/ML code/MarketPlaceServer/app/data/waste_recommender_model.joblib'

try:
    APP_STATE = {
        'CROP_DF': pd.read_csv(DATA_PATH + 'crop_npk_requirements.csv'),
        'OFFERS_DF': pd.read_csv(DATA_PATH + 'offers.csv'),
        'PRODUCER_DF': pd.read_csv(DATA_PATH + 'waste_producers.csv'),
        'WASTE_DF_PROCESSED': pd.read_csv(DATA_PATH + 'waste_npk_processed.csv'),
        'WASTE_MODEL': joblib.load(MODEL_PATH),
    }
except FileNotFoundError as e:
    print(f"CRITICAL ERROR: Data or Model missing. Please check {DATA_PATH} directory.")
    raise e

app = FastAPI(title="Waste-to-Fertilizer Bargain API") 
