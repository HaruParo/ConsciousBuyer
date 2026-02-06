"""
Vercel Serverless Function - Main API Handler
"""

import sys
from pathlib import Path

# Add project paths FIRST before any imports
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    # Import the full FastAPI app from api/main.py
    from api.main import app
except Exception as e:
    # If import fails, create a minimal app that shows the error
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    error_message = str(e)

    @app.get("/api")
    @app.get("/api/{path:path}")
    @app.post("/api/{path:path}")
    def error_handler(path: str = ""):
        return {
            "error": "API failed to load",
            "detail": error_message,
            "path": path
        }
