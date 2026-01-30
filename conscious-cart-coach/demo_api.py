#!/usr/bin/env python3
"""
Quick FastAPI demo for Store Classification System
Run: python demo_api.py
Then visit: http://localhost:8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import sys
import importlib.util

# Load store split modules
def load_module(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

orchestrator_path = '/Users/hash/Documents/ConsciousBuyer/conscious-cart-coach/src/orchestrator'
sys.path.insert(0, orchestrator_path)

ingredient_classifier = load_module('ingredient_classifier', f'{orchestrator_path}/ingredient_classifier.py')
store_split_module = load_module('store_split', f'{orchestrator_path}/store_split.py')

classify_ingredient_store_type = ingredient_classifier.classify_ingredient_store_type
split_ingredients_by_store = store_split_module.split_ingredients_by_store
format_store_split_for_ui = store_split_module.format_store_split_for_ui
UserPreferences = store_split_module.UserPreferences

app = FastAPI(title="Conscious Cart Coach - Store Classification Demo")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StoreSplitRequest(BaseModel):
    ingredients: List[str]
    urgency: Optional[str] = "planning"  # "planning" or "urgent"

@app.get("/", response_class=HTMLResponse)
def demo_ui():
    """Interactive demo UI"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Store Classification Demo</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: #fef9f5;
                padding: 40px 20px;
            }
            .container { max-width: 900px; margin: 0 auto; }
            h1 { color: #6b5f3a; margin-bottom: 8px; }
            .subtitle { color: #999; margin-bottom: 32px; }
            .input-section {
                background: white;
                padding: 24px;
                border-radius: 12px;
                margin-bottom: 24px;
                border: 2px solid #e5d5b8;
            }
            label {
                display: block;
                font-weight: 600;
                color: #6b5f3a;
                margin-bottom: 8px;
            }
            textarea {
                width: 100%;
                padding: 12px;
                border: 2px solid #e5d5b8;
                border-radius: 8px;
                font-size: 14px;
                font-family: inherit;
                resize: vertical;
            }
            .urgency-toggle {
                display: flex;
                gap: 12px;
                margin-top: 16px;
            }
            .urgency-toggle button {
                flex: 1;
                padding: 12px;
                border: 2px solid #e5d5b8;
                border-radius: 8px;
                background: white;
                cursor: pointer;
                font-weight: 600;
                transition: all 0.2s;
            }
            .urgency-toggle button.active {
                background: #6b5f3a;
                color: white;
                border-color: #6b5f3a;
            }
            button.submit {
                width: 100%;
                padding: 16px;
                background: #6b5f3a;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 16px;
                cursor: pointer;
                margin-top: 16px;
            }
            button.submit:hover { background: #5a4f2f; }
            .results { display: none; }
            .results.show { display: block; }
            .store-tabs {
                display: flex;
                gap: 12px;
                margin-bottom: 24px;
            }
            .store-tab {
                flex: 1;
                padding: 16px;
                background: white;
                border-radius: 12px;
                border: 3px solid;
            }
            .store-tab.primary { border-color: #d4976c; }
            .store-tab.specialty { border-color: #8b7ba8; }
            .store-tab.unavailable { border-color: #e5d5b8; }
            .store-tab-label {
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 8px;
            }
            .store-tab.primary .store-tab-label { color: #d4976c; }
            .store-tab.specialty .store-tab-label { color: #8b7ba8; }
            .store-tab.unavailable .store-tab-label { color: #a89968; }
            .store-count {
                font-size: 32px;
                font-weight: 700;
                color: #333;
                margin-bottom: 4px;
            }
            .store-name {
                font-size: 12px;
                color: #666;
            }
            .ingredients-list {
                background: white;
                padding: 20px;
                border-radius: 12px;
                border: 2px solid #e5d5b8;
            }
            .ingredient-item {
                padding: 12px;
                border-bottom: 1px solid #f0f0f0;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .ingredient-item:last-child { border-bottom: none; }
            .badge {
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
            }
            .badge.primary { background: #fef3e6; color: #d4976c; }
            .badge.specialty { background: #f3f0f7; color: #8b7ba8; }
            .badge.both { background: #f5f5f5; color: #666; }
            .alert {
                background: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 12px;
                margin-bottom: 16px;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛒 Store Classification Demo</h1>
            <p class="subtitle">Dynamic ingredient classification with 1-item rule</p>

            <div class="input-section">
                <label>Enter ingredients (one per line or comma-separated):</label>
                <textarea id="ingredients" rows="6" placeholder="chicken&#10;spinach&#10;turmeric&#10;cumin&#10;ghee">chicken, onions, tomatoes, yogurt, cilantro, turmeric, cumin, coriander, garam_masala, basmati_rice, ghee</textarea>

                <label style="margin-top: 16px;">Urgency:</label>
                <div class="urgency-toggle">
                    <button id="urgency-planning" class="active" onclick="setUrgency('planning')">
                        📅 Planning (1-2 weeks)
                    </button>
                    <button id="urgency-urgent" onclick="setUrgency('urgent')">
                        ⚡ Urgent (1-2 days)
                    </button>
                </div>

                <button class="submit" onclick="classify()">Classify Ingredients</button>
            </div>

            <div id="results" class="results"></div>
        </div>

        <script>
            let urgency = 'planning';

            function setUrgency(value) {
                urgency = value;
                document.getElementById('urgency-planning').classList.toggle('active', value === 'planning');
                document.getElementById('urgency-urgent').classList.toggle('active', value === 'urgent');
            }

            async function classify() {
                const text = document.getElementById('ingredients').value;
                const ingredients = text.split(/[,\\n]/).map(s => s.trim()).filter(s => s);

                const response = await fetch('/api/store-split', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ ingredients, urgency })
                });

                const data = await response.json();
                displayResults(data);
            }

            function displayResults(data) {
                const ui = data.ui_format;
                const split = data.store_split;

                let html = '<div class="store-tabs">';
                html += `
                    <div class="store-tab primary">
                        <div class="store-tab-label">Primary Store</div>
                        <div class="store-count">${ui.primary_store.count}</div>
                        <div class="store-name">${ui.primary_store.store}</div>
                    </div>
                    <div class="store-tab specialty">
                        <div class="store-tab-label">Specialty Store</div>
                        <div class="store-count">${ui.specialty_store.count}</div>
                        <div class="store-name">${ui.specialty_store.store}</div>
                    </div>
                    <div class="store-tab unavailable">
                        <div class="store-tab-label">Unavailable</div>
                        <div class="store-count">${ui.unavailable.length}</div>
                        <div class="store-name">Not in stock</div>
                    </div>
                </div>`;

                if (split.applied_1_item_rule) {
                    html += `<div class="alert">💡 1-item efficiency rule: Merged specialty items to primary store</div>`;
                }

                html += '<div class="ingredients-list">';
                data.classifications.forEach(item => {
                    const badgeClass = item.store_type === 'primary' ? 'primary' :
                                      item.store_type === 'specialty' ? 'specialty' : 'both';
                    html += `
                        <div class="ingredient-item">
                            <span>${item.ingredient}</span>
                            <span class="badge ${badgeClass}">${item.store_type}</span>
                        </div>
                    `;
                });
                html += '</div>';

                document.getElementById('results').innerHTML = html;
                document.getElementById('results').classList.add('show');
            }
        </script>
    </body>
    </html>
    """

@app.post("/api/store-split")
def api_store_split(request: StoreSplitRequest):
    """API endpoint for store split classification"""
    # Mock candidates (in real app, this would come from ProductAgent)
    candidates = {ing: [{"id": f"{ing}_001"}] for ing in request.ingredients}

    # User preferences
    user_prefs = UserPreferences(urgency=request.urgency)

    # Classify
    store_split = split_ingredients_by_store(request.ingredients, candidates, user_prefs)
    ui_format = format_store_split_for_ui(store_split)

    # Get individual classifications
    classifications = []
    for ing in request.ingredients:
        store_type = classify_ingredient_store_type(ing)
        classifications.append({
            "ingredient": ing,
            "store_type": store_type
        })

    return {
        "store_split": {
            "total_stores_needed": store_split.total_stores_needed,
            "applied_1_item_rule": store_split.applied_1_item_rule,
            "reasoning": store_split.reasoning
        },
        "ui_format": ui_format,
        "classifications": classifications
    }

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🛒 CONSCIOUS CART COACH - STORE CLASSIFICATION DEMO")
    print("="*60)
    print("\n📍 Demo UI: http://localhost:8000")
    print("📍 API Docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
