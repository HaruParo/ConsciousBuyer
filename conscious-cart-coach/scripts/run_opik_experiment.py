#!/usr/bin/env python3
"""
Opik Experiment Runner for Conscious Cart Coach

Run experiments to evaluate LLM performance on ingredient extraction
and decision explanations.

Usage:
    # Set environment first
    export DEPLOYMENT_ENV=cloud
    export ANTHROPIC_API_KEY=sk-ant-...
    export OPIK_API_KEY=...

    # Run experiment
    python scripts/run_opik_experiment.py

    # Run specific experiment
    python scripts/run_opik_experiment.py --experiment ingredient_extraction
    python scripts/run_opik_experiment.py --experiment decision_explanation
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Force cloud for experiments
os.environ["DEPLOYMENT_ENV"] = "cloud"

import opik
from opik import Opik, track
from opik.evaluation import evaluate
from opik.evaluation.metrics import Equals, Contains, LevenshteinRatio
from opik.evaluation.metrics.base_metric import BaseMetric
from opik.evaluation.metrics.score_result import ScoreResult

# Initialize Opik
opik.configure(
    api_key=os.environ.get("OPIK_API_KEY"),
    workspace=os.environ.get("OPIK_WORKSPACE", "default"),
)

# =============================================================================
# TEST DATASETS
# =============================================================================

INGREDIENT_EXTRACTION_DATASET = [
    {
        "input": "chicken biryani for 4",
        "expected_ingredients": ["chicken", "basmati rice", "onion", "yogurt", "ginger", "garlic"],
        "min_count": 6,
        "cuisine": "indian",
    },
    {
        "input": "spaghetti carbonara for 2",
        "expected_ingredients": ["spaghetti", "eggs", "parmesan", "pancetta", "black pepper"],
        "min_count": 4,
        "cuisine": "italian",
    },
    {
        "input": "chicken tacos for 6",
        "expected_ingredients": ["chicken", "tortillas", "onion", "cilantro", "lime"],
        "min_count": 4,
        "cuisine": "mexican",
    },
    {
        "input": "vegetable stir fry for 2",
        "expected_ingredients": ["broccoli", "carrot", "soy sauce", "garlic", "ginger"],
        "min_count": 4,
        "cuisine": "asian",
    },
    {
        "input": "greek salad for 4",
        "expected_ingredients": ["cucumber", "tomato", "feta", "olives", "olive oil"],
        "min_count": 4,
        "cuisine": "mediterranean",
    },
]

DECISION_EXPLANATION_DATASET = [
    {
        "ingredient": "spinach",
        "product": {"brand": "Earthbound Farm", "price": 3.99, "size": "5 oz", "organic": True},
        "scoring_factors": ["organic: +20", "EWG Dirty Dozen: +15"],
        "cheaper_option": "Store brand at $2.49",
        "should_mention": ["organic", "Dirty Dozen"],
    },
    {
        "ingredient": "chicken thighs",
        "product": {"brand": "Bell & Evans", "price": 8.99, "size": "1 lb", "organic": False},
        "scoring_factors": ["air-chilled: +10", "no antibiotics: +15"],
        "cheaper_option": "Perdue at $5.99",
        "should_mention": ["quality", "price"],
    },
    {
        "ingredient": "olive oil",
        "product": {"brand": "California Olive Ranch", "price": 12.99, "size": "500ml", "organic": False},
        "scoring_factors": ["California origin: +10", "fresh harvest: +5"],
        "cheaper_option": "Store brand at $7.99",
        "should_mention": ["California", "quality"],
    },
]


# =============================================================================
# EVALUATION TASKS
# =============================================================================

@track
def extract_ingredients_task(input_prompt: str) -> dict:
    """Run ingredient extraction and return results."""
    from src.llm.ingredient_extractor import extract_ingredients_with_llm
    from src.utils.llm_client import get_llm_client

    client = get_llm_client()
    result = extract_ingredients_with_llm(
        client=client,
        prompt=input_prompt,
        servings=4,
    )

    return {
        "ingredients": result if result else [],
        "raw_response": result,
    }


@track
def generate_explanation_task(
    ingredient: str,
    product: dict,
    scoring_factors: list,
    cheaper_option: str,
) -> dict:
    """Run decision explanation and return results."""
    from src.llm.decision_explainer import explain_decision_with_llm
    from src.utils.llm_client import get_llm_client

    client = get_llm_client()
    explanation = explain_decision_with_llm(
        client=client,
        ingredient_name=ingredient,
        recommended_product=product,
        scoring_factors=scoring_factors,
        cheaper_option=cheaper_option,
    )

    return {
        "explanation": explanation or "",
        "length": len(explanation) if explanation else 0,
    }


# =============================================================================
# CUSTOM METRICS (Opik-compatible)
# =============================================================================

class IngredientCoverageMetric(BaseMetric):
    """Score based on how many expected ingredients were extracted."""

    def __init__(self):
        super().__init__(name="ingredient_coverage")

    def score(self, ingredients: list, expected_ingredients: list, **kwargs) -> ScoreResult:
        extracted = [i.get("name", "").lower() for i in ingredients]
        expected_list = [e.lower() for e in expected_ingredients]

        if not expected_list:
            return ScoreResult(value=1.0, name=self.name)

        matches = sum(1 for e in expected_list if any(e in ext for ext in extracted))
        score = matches / len(expected_list)
        return ScoreResult(value=score, name=self.name)


class IngredientCountMetric(BaseMetric):
    """Score based on meeting minimum ingredient count."""

    def __init__(self):
        super().__init__(name="ingredient_count")

    def score(self, ingredients: list, min_count: int, **kwargs) -> ScoreResult:
        count = len(ingredients)

        if count >= min_count:
            score = 1.0
        else:
            score = count / min_count
        return ScoreResult(value=score, name=self.name)


class ExplanationQualityMetric(BaseMetric):
    """Score based on explanation mentioning key terms."""

    def __init__(self):
        super().__init__(name="explanation_quality")

    def score(self, explanation: str, should_mention: list, **kwargs) -> ScoreResult:
        explanation_lower = explanation.lower() if explanation else ""

        if not should_mention:
            return ScoreResult(value=1.0, name=self.name)

        matches = sum(1 for term in should_mention if term.lower() in explanation_lower)
        score = matches / len(should_mention)
        return ScoreResult(value=score, name=self.name)


class ExplanationLengthMetric(BaseMetric):
    """Score based on explanation being concise (1-2 sentences)."""

    def __init__(self):
        super().__init__(name="explanation_length")

    def score(self, explanation: str, **kwargs) -> ScoreResult:
        length = len(explanation) if explanation else 0

        # Ideal: 50-150 chars (1-2 sentences)
        if 50 <= length <= 150:
            score = 1.0
        elif 30 <= length <= 200:
            score = 0.7
        elif length > 0:
            score = 0.3
        else:
            score = 0.0
        return ScoreResult(value=score, name=self.name)


# =============================================================================
# EXPERIMENT RUNNERS
# =============================================================================

def run_ingredient_extraction_experiment():
    """Run ingredient extraction experiment using Opik evaluate()."""
    print("\n" + "="*60)
    print("INGREDIENT EXTRACTION EXPERIMENT")
    print("="*60)

    client = Opik()

    # Create or get dataset
    dataset_name = "ingredient_extraction_test"
    try:
        dataset = client.get_dataset(dataset_name)
        print(f"Using existing dataset: {dataset_name}")
    except:
        dataset = client.create_dataset(dataset_name)
        for item in INGREDIENT_EXTRACTION_DATASET:
            dataset.insert([{
                "input": item["input"],
                "expected_ingredients": item["expected_ingredients"],
                "min_count": item["min_count"],
                "cuisine": item["cuisine"],
            }])
        print(f"Created dataset: {dataset_name} with {len(INGREDIENT_EXTRACTION_DATASET)} items")

    # Define evaluation task
    def evaluation_task(item: dict) -> dict:
        print(f"\nTesting: {item['input']}")
        output = extract_ingredients_task(item["input"])
        print(f"  Extracted: {len(output.get('ingredients', []))} ingredients")
        return output

    # Run evaluation with Opik
    results = evaluate(
        experiment_name="ingredient_extraction",
        dataset=dataset,
        task=evaluation_task,
        scoring_metrics=[
            IngredientCoverageMetric(),
            IngredientCountMetric(),
        ],
    )

    print("\n" + "-"*60)
    print("EXPERIMENT COMPLETE - View results in Opik dashboard")
    print("-"*60)

    return results


def run_decision_explanation_experiment():
    """Run decision explanation experiment using Opik evaluate()."""
    print("\n" + "="*60)
    print("DECISION EXPLANATION EXPERIMENT")
    print("="*60)

    client = Opik()

    # Create or get dataset
    dataset_name = "decision_explanation_test"
    try:
        dataset = client.get_dataset(dataset_name)
        print(f"Using existing dataset: {dataset_name}")
    except:
        dataset = client.create_dataset(dataset_name)
        for item in DECISION_EXPLANATION_DATASET:
            dataset.insert([{
                "ingredient": item["ingredient"],
                "product": item["product"],
                "scoring_factors": item["scoring_factors"],
                "cheaper_option": item["cheaper_option"],
                "should_mention": item["should_mention"],
            }])
        print(f"Created dataset: {dataset_name} with {len(DECISION_EXPLANATION_DATASET)} items")

    # Define evaluation task
    def evaluation_task(item: dict) -> dict:
        print(f"\nTesting: {item['ingredient']}")
        output = generate_explanation_task(
            ingredient=item["ingredient"],
            product=item["product"],
            scoring_factors=item["scoring_factors"],
            cheaper_option=item["cheaper_option"],
        )
        explanation = output.get("explanation", "")
        print(f"  Explanation: {explanation[:80]}..." if len(explanation) > 80 else f"  Explanation: {explanation}")
        return output

    # Run evaluation with Opik
    results = evaluate(
        experiment_name="decision_explanation",
        dataset=dataset,
        task=evaluation_task,
        scoring_metrics=[
            ExplanationQualityMetric(),
            ExplanationLengthMetric(),
        ],
    )

    print("\n" + "-"*60)
    print("EXPERIMENT COMPLETE - View results in Opik dashboard")
    print("-"*60)

    return results


def run_all_experiments():
    """Run all experiments."""
    print("\n" + "#"*60)
    print("# OPIK EXPERIMENT RUNNER - Conscious Cart Coach")
    print("#"*60)

    ingredient_results = run_ingredient_extraction_experiment()
    explanation_results = run_decision_explanation_experiment()

    print("\n" + "="*60)
    print("ALL EXPERIMENTS COMPLETE")
    print("="*60)
    print(f"\nView results at: https://app.comet.com/opik")

    return {
        "ingredient_extraction": ingredient_results,
        "decision_explanation": explanation_results,
    }


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Opik experiments")
    parser.add_argument(
        "--experiment",
        choices=["ingredient_extraction", "decision_explanation", "all"],
        default="all",
        help="Which experiment to run",
    )
    args = parser.parse_args()

    # Check environment
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set")
        print("Run: export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    if not os.environ.get("OPIK_API_KEY"):
        print("WARNING: OPIK_API_KEY not set - results won't be uploaded to Opik")
        print("Run: export OPIK_API_KEY=...")

    # Run experiments
    if args.experiment == "ingredient_extraction":
        run_ingredient_extraction_experiment()
    elif args.experiment == "decision_explanation":
        run_decision_explanation_experiment()
    else:
        run_all_experiments()
