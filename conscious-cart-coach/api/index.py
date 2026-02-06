"""
Vercel Serverless Function - Main API Handler
Vercel's Python runtime natively supports FastAPI/ASGI apps
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
from pathlib import Path

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Create FastAPI app
app = FastAPI(title="Conscious Cart Coach API", version="1.0.0")

# CORS - allow all for Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class CreateCartRequest(BaseModel):
    meal_plan: str
    servings: int = 2

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str

# Health check
@app.get("/", response_model=HealthResponse)
@app.get("/api", response_model=HealthResponse)
def health():
    return {
        "status": "ok",
        "service": "Conscious Cart Coach API",
        "version": "1.0.0"
    }

# Import full routes if available
try:
    from src.orchestrator.orchestrator import Orchestrator
    from src.contracts.models import DecisionBundle

    @app.post("/api/create-cart")
    def create_cart(request: CreateCartRequest):
        """Create shopping cart from meal plan."""
        try:
            orch = Orchestrator(use_llm_extraction=False, use_llm_explanations=False)
            result = orch.step_ingredients(request.meal_plan, servings=request.servings)

            if result.status != "ok":
                raise HTTPException(status_code=400, detail="Failed to extract ingredients")

            ingredients = result.facts.get("ingredients", [])
            orch.confirm_ingredients(ingredients)
            orch.step_candidates()
            orch.step_enrich()
            bundle = orch.step_decide()

            # Format response
            items = []
            total = 0.0
            for idx, item in enumerate(bundle.items or []):
                price = 5.99  # Default price
                items.append({
                    "id": f"item-{idx}",
                    "name": item.ingredient_name,
                    "price": price,
                    "quantity": 1
                })
                total += price

            return {
                "items": items,
                "total": round(total, 2),
                "store": "FreshDirect",
                "servings": request.servings
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/extract-ingredients")
    def extract_ingredients(request: CreateCartRequest):
        """Extract ingredients from meal plan."""
        try:
            orch = Orchestrator(use_llm_extraction=False, use_llm_explanations=False)
            result = orch.step_ingredients(request.meal_plan, servings=request.servings)

            if result.status != "ok":
                raise HTTPException(status_code=400, detail="Failed to extract ingredients")

            ingredients = result.facts.get("ingredients", [])
            return {
                "ingredients": ingredients,
                "servings": request.servings
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

except ImportError as e:
    @app.get("/api/status")
    def import_error():
        return {"status": "limited", "error": str(e)}
