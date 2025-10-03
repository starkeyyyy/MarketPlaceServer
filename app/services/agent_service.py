from fastapi import APIRouter

router = APIRouter(prefix="/agent", tags=["Agent"])

@router.get("/hello")
def hello_agent():
    """Simple endpoint to test agent service."""
    return {"message": "Hello from Agent Service!"}
