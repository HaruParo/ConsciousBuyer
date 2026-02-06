"""
Vercel Serverless Function Handler
Exposes FastAPI app for Vercel's Python runtime
"""

import sys
from pathlib import Path

# Add paths for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

# Create a minimal app for Vercel
app = FastAPI(title="Conscious Cart Coach API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
@app.get("/api")
def health():
    return {"status": "ok", "service": "Conscious Cart Coach API", "version": "1.0.0"}

# Try to import full API routes, fall back to minimal if dependencies missing
try:
    from api.main import app as full_app
    # Copy routes from full app
    app.routes.extend(full_app.routes)
except ImportError as e:
    @app.get("/api/status")
    def status():
        return {"error": f"Full API not available: {str(e)}"}

# Vercel handler
handler = Mangum(app, lifespan="off")
