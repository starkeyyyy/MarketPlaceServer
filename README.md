# FastAPI Starter Boilerplate

This is a simple FastAPI boilerplate to help you start building a FastAPI application with a clean structure.

## Structure

- `run.py`: Entry point for running the FastAPI app using Uvicorn.
- `services/`: Folder for organizing your business logic and API routers.
  - `agent_service.py`: Example service with a router for agent-related endpoints.
- `requirements.txt`: List of required Python packages.

## How to Start

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
2. **Run the application**
   ```bash
   python run.py
   ```
   The server will start at `http://localhost:8000`.

## How It Works

- `run.py` creates a FastAPI app and includes routers from the `services` folder.
- Each service (like `agent_service.py`) defines a router with endpoints for a specific domain (e.g., agent operations).
- You can add more services by creating new files in the `services` folder and including their routers in `run.py`.

## Extending

- Add new routers/services in the `services` folder.
- Use dependency injection, middleware, and other FastAPI features as needed.

---
This boilerplate is designed for clarity and quick prototyping. Expand as your project grows!
