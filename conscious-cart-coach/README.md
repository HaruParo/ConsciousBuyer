# Conscious Cart Coach

Make more conscious purchasing decisions by analyzing your receipts and getting personalized recommendations for ethical and sustainable alternatives.

## Features

- **Receipt Analysis**: Upload CSV receipts to analyze your purchasing patterns
- **Baseline Tracking**: Establish your baseline and track improvements over time
- **Smart Recommendations**: LLM-powered suggestions for ethical/sustainable alternatives
- **Impact Tracking**: See the environmental and ethical impact of your choices
- **Experiment Tracking**: A/B test different recommendation strategies with Opik

## Project Structure

```
conscious-cart-coach/
├── data/
│   ├── raw/              # Original receipts CSV
│   ├── processed/        # Normalized data
│   ├── alternatives/     # Manual seed data
│   └── opik_logs/        # Evaluation data
├── src/
│   ├── data_processing/  # Data ingestion and validation
│   ├── llm/              # Decision engine and explainer
│   ├── opik_integration/ # Tracking and experiments
│   └── ui/               # Streamlit web interface
├── tests/
│   └── test_scenarios/
└── ...
```

## Setup

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd conscious-cart-coach
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. Run the application:
   ```bash
   ./run.sh
   ```

## Configuration

Copy `.env.example` to `.env` and fill in your credentials:

- `ANTHROPIC_API_KEY`: Your Anthropic API key for Claude
- `OPIK_API_KEY`: Your Opik API key for tracking
- `DATABASE_URL`: PostgreSQL connection string

## Usage

1. Start the Streamlit app with `./run.sh`
2. Upload your receipt CSV files
3. Review your baseline purchasing patterns
4. Get recommendations for ethical alternatives
5. Track your progress over time

## Development

Run tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=src
```

## License

MIT
