# app/config/api.py

from fastapi import FastAPI
from app.routes.uploads.photo_upload import router as upload_router
from starlette.middleware.cors import CORSMiddleware
# ... other imports (Pandas, joblib, etc. for the real app) ...

# NOTE: Minimal placeholder for APP_STATE to prevent crashes
APP_STATE = {
    'WASTE_DF_PROCESSED': None # Will be loaded in a real service
}

app = FastAPI(title="Waste Analysis Interface")

# Include the file upload router
app.include_router(upload_router, prefix="/api/v1") 

# Add CORS middleware (essential for frontend testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)