Create a Python project for "Conscious Cart Coach" with this structure:

conscious-cart-coach/
├── data/
│   ├── raw/              # Original receipts CSV
│   ├── processed/        # Normalized data
│   ├── alternatives/     # Manual seed data
│   └── opik_logs/        # Evaluation data
├── src/
│   ├── data_processing/
│   │   ├── __init__.py
│   │   ├── ingest.py
│   │   ├── baseline.py
│   │   ├── facts_pack.py
│   │   └── validator.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── decision_engine.py
│   │   └── explainer.py
│   ├── opik_integration/
│   │   ├── __init__.py
│   │   ├── tracker.py
│   │   └── experiments.py
│   └── ui/
│       ├── __init__.py
│       └── app.py
├── tests/
│   └── test_scenarios/
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── run.sh

Initialize git repo.

Create requirements.txt with:
- pandas
- sqlalchemy
- psycopg2-binary
- anthropic (or openai)
- opik-python
- streamlit
- python-dotenv
- pytest

Create .gitignore for Python (add .env, data/raw/, __pycache__)

Create .env.example with:
ANTHROPIC_API_KEY=your_key_here
OPIK_API_KEY=your_key_here
DATABASE_URL=postgresql://localhost/conscious_cart

Create run.sh that sets PYTHONPATH and runs streamlit
