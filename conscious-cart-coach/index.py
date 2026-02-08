"""
Vercel Serverless Function - Main API Handler
"""

import os
import sys
from pathlib import Path

# Add project paths FIRST before any imports
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    # Import the full FastAPI app from api/main.py
    from api.main import app

    # Add debug endpoint to check env vars
    @app.get("/api/debug-env")
    def debug_env():
        return {
            "VERCEL": os.environ.get("VERCEL", "not set"),
            "DEPLOYMENT_ENV": os.environ.get("DEPLOYMENT_ENV", "not set"),
            "LLM_PROVIDER": os.environ.get("LLM_PROVIDER", "not set"),
            "ANTHROPIC_API_KEY": "set" if os.environ.get("ANTHROPIC_API_KEY") else "NOT SET",
            "GOOGLE_API_KEY": "set" if os.environ.get("GOOGLE_API_KEY") else "NOT SET",
            "OPIK_API_KEY": "set" if os.environ.get("OPIK_API_KEY") else "NOT SET",
        }

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
