from fastapi import FastAPI
from app.services.agent_service import router as agent_router

app = FastAPI()

# Include routers from services
app.include_router(agent_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
