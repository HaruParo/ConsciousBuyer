#!/usr/bin/env python3
"""
LLM Extraction Evaluation Harness

Tests ingredient extraction across different models and measures:
- Precision: How many extracted ingredients are correct
- Recall: How many expected ingredients were found
- Stability: Consistency across multiple runs

Usage:
    python scripts/eval_llm_extraction.py
    python scripts/eval_llm_extraction.py --model mistral
    python scripts/eval_llm_extraction.py --compare mistral claude-haiku
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.llm.ingredient_extractor import IngredientExtractor
except ImportError:
    print("⚠️  IngredientExtractor not found, using mock")
    IngredientExtractor = None


# ============================================================================
# Mock Extractor (for testing without LLM)
# ============================================================================

class MockExtractor:
    """Mock extractor that returns reasonable default ingredients"""

    def extract(self, prompt: str) -> Dict:
        """Mock extraction based on keywords"""
        prompt_lower = prompt.lower()

        if "biryani" in prompt_lower:
            ingredients = [
                {"name": "chicken", "quantity": 1.5, "unit": "lb"},
                {"name": "rice", "quantity": 2, "unit": "cups"},
                {"name": "onions", "quantity": 2, "unit": "medium"},
                {"name": "ginger", "quantity": 2, "unit": "inches"},
                {"name": "garlic", "quantity": 8, "unit": "cloves"},
            ]
        elif "pasta" in prompt_lower:
            ingredients = [
                {"name": "pasta", "quantity": 1, "unit": "lb"},
                {"name": "tomatoes", "quantity": 2, "unit": "cups"},
                {"name": "garlic", "quantity": 4, "unit": "cloves"},
            ]
        elif "tacos" in prompt_lower:
            ingredients = [
                {"name": "ground beef", "quantity": 1, "unit": "lb"},
                {"name": "taco shells", "quantity": 12, "unit": "shells"},
                {"name": "lettuce", "quantity": 1, "unit": "head"},
            ]
        else:
            ingredients = [
                {"name": "generic ingredient", "quantity": 1, "unit": "unit"}
            ]

        # Extract servings
        servings = 2  # default
        if "for 4" in prompt_lower or "4 people" in prompt_lower:
            servings = 4
        elif "for 6" in prompt_lower:
            servings = 6

        return {
            "ingredients": ingredients,
            "servings": servings
        }


# ============================================================================
# Scoring Functions
# ============================================================================

def normalize_ingredient(name: str) -> str:
    """Normalize ingredient name for comparison"""
    # Remove common variations
    name = name.lower().strip()
    name = name.replace("fresh ", "")
    name = name.replace("organic ", "")
    name = name.replace(" leaves", "")
    name = name.replace(" powder", "")

    # Map synonyms
    synonyms = {
        "cilantro": "coriander leaves",
        "scallions": "green onions",
        "basmati rice": "rice",
    }

    for key, value in synonyms.items():
        if key in name:
            name = value

    return name


def calculate_precision_recall(
    extracted: List[str],
    expected: List[str],
    override_mode: bool = False
) -> Dict[str, float]:
    """
    Calculate precision and recall

    Precision = correct / extracted
    Recall = correct / expected

    In override_mode, also track missing and extra ingredients
    """
    # Normalize names
    extracted_norm = {normalize_ingredient(name) for name in extracted}
    expected_norm = {normalize_ingredient(name) for name in expected}

    # Find matches
    matches = extracted_norm & expected_norm

    # Track missing and extra items (useful for override mode)
    missing = expected_norm - extracted_norm
    extra = extracted_norm - expected_norm

    precision = len(matches) / len(extracted_norm) if extracted_norm else 0.0
    recall = len(matches) / len(expected_norm) if expected_norm else 0.0

    f1 = (2 * precision * recall / (precision + recall)
          if (precision + recall) > 0 else 0.0)

    result = {
        "precision": round(precision * 100, 1),
        "recall": round(recall * 100, 1),
        "f1": round(f1 * 100, 1),
        "matches": len(matches),
        "extracted_count": len(extracted_norm),
        "expected_count": len(expected_norm)
    }

    # Add missing/extra for override mode debugging
    if override_mode:
        result["missing"] = list(missing)
        result["extra"] = list(extra)
        result["exact_match"] = len(missing) == 0 and len(extra) == 0

    return result


def check_critical_ingredients(
    extracted: List[str],
    critical: List[str]
) -> Dict:
    """Check if critical ingredients are present"""
    extracted_norm = {normalize_ingredient(name) for name in extracted}
    critical_norm = {normalize_ingredient(name) for name in critical}

    found = extracted_norm & critical_norm
    missing = critical_norm - extracted_norm

    return {
        "all_found": len(missing) == 0,
        "found_count": len(found),
        "missing": list(missing)
    }


# ============================================================================
# Test Runner
# ============================================================================

def load_test_cases(test_file: Path) -> List[Dict]:
    """Load test cases from JSON file"""
    if not test_file.exists():
        print(f"⚠️  Test file not found: {test_file}")
        return []

    with open(test_file) as f:
        return json.load(f)


def run_evaluation(
    extractor,
    test_cases: List[Dict],
    model_name: str = "unknown",
    num_runs: int = 1
) -> Dict:
    """
    Run evaluation on test cases

    Args:
        extractor: Ingredient extractor instance
        test_cases: List of test case dicts
        model_name: Name of model being tested
        num_runs: Number of times to run each test (for stability check)

    Returns:
        Dict with aggregate scores
    """
    results = []
    stability_scores = []
    override_results = []

    for test_case in test_cases:
        test_id = test_case["id"]
        prompt = test_case["prompt"]
        expected = test_case["expected_ingredients"]
        critical = test_case.get("critical_ingredients", [])
        override_mode = test_case.get("override_mode", False) or "INGREDIENT_LIST:" in prompt

        print(f"\nTest {test_id}: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
        if override_mode:
            print("  [OVERRIDE MODE - Strict Compliance Required]")
        print("-" * 60)

        # Run multiple times for stability check
        run_outputs = []
        for run_idx in range(num_runs):
            try:
                output = extractor.extract(prompt)
                extracted_names = [ing["name"] for ing in output["ingredients"]]
                run_outputs.append(extracted_names)

                if run_idx == 0:  # Only show first run
                    print(f"  Extracted: {', '.join(extracted_names[:5])}" +
                          (f", ... ({len(extracted_names)} total)" if len(extracted_names) > 5 else ""))

            except Exception as e:
                print(f"  ❌ Extraction failed: {e}")
                run_outputs.append([])

        # Use first run for scoring
        extracted = run_outputs[0] if run_outputs else []

        # Calculate scores
        scores = calculate_precision_recall(extracted, expected, override_mode=override_mode)
        critical_check = check_critical_ingredients(extracted, critical)

        # Stability: Check if all runs produced same output
        if num_runs > 1:
            stability = all(set(run) == set(run_outputs[0]) for run in run_outputs)
            stability_scores.append(stability)
            print(f"  Stability: {'✓' if stability else '✗'}")

        # Print scores
        print(f"  Precision: {scores['precision']}%")
        print(f"  Recall: {scores['recall']}%")
        print(f"  F1: {scores['f1']}%")

        # Override mode: strict compliance check
        if override_mode:
            exact_match = scores.get("exact_match", False)
            if exact_match:
                print(f"  ✅ Override Compliance: PASS (exact match)")
            else:
                print(f"  ❌ Override Compliance: FAIL")
                if scores.get("missing"):
                    print(f"     Missing: {scores['missing']}")
                if scores.get("extra"):
                    print(f"     Extra: {scores['extra']}")

            override_results.append({
                "test_id": test_id,
                "passed": exact_match
            })

        if not critical_check["all_found"]:
            print(f"  ⚠️  Missing critical: {critical_check['missing']}")

        results.append({
            "test_id": test_id,
            "prompt": prompt,
            "scores": scores,
            "critical_check": critical_check,
            "override_mode": override_mode
        })

    # Aggregate scores
    avg_precision = sum(r["scores"]["precision"] for r in results) / len(results)
    avg_recall = sum(r["scores"]["recall"] for r in results) / len(results)
    avg_f1 = sum(r["scores"]["f1"] for r in results) / len(results)

    critical_pass_rate = sum(1 for r in results if r["critical_check"]["all_found"]) / len(results) * 100

    stability_rate = (sum(stability_scores) / len(stability_scores) * 100
                      if stability_scores else 0)

    # Override compliance metrics
    override_compliance = None
    if override_results:
        override_pass_count = sum(1 for r in override_results if r["passed"])
        override_compliance = {
            "total_override_cases": len(override_results),
            "passed": override_pass_count,
            "failed": len(override_results) - override_pass_count,
            "pass_rate": round(override_pass_count / len(override_results) * 100, 1)
        }

    return {
        "model": model_name,
        "num_tests": len(results),
        "avg_precision": round(avg_precision, 1),
        "avg_recall": round(avg_recall, 1),
        "avg_f1": round(avg_f1, 1),
        "critical_pass_rate": round(critical_pass_rate, 1),
        "stability_rate": round(stability_rate, 1) if stability_scores else None,
        "override_compliance": override_compliance,
        "details": results
    }


def print_summary(evaluation: Dict):
    """Print evaluation summary"""
    print("\n" + "=" * 60)
    print(f"EVALUATION SUMMARY: {evaluation['model']}")
    print("=" * 60)
    print(f"Tests run: {evaluation['num_tests']}")
    print(f"Average Precision: {evaluation['avg_precision']}%")
    print(f"Average Recall: {evaluation['avg_recall']}%")
    print(f"Average F1 Score: {evaluation['avg_f1']}%")
    print(f"Critical Ingredients Pass Rate: {evaluation['critical_pass_rate']}%")

    if evaluation['stability_rate'] is not None:
        print(f"Stability Rate: {evaluation['stability_rate']}%")

    # Override compliance section
    if evaluation['override_compliance']:
        oc = evaluation['override_compliance']
        print(f"\nOverride Compliance:")
        print(f"  Total override cases: {oc['total_override_cases']}")
        print(f"  Passed: {oc['passed']}")
        print(f"  Failed: {oc['failed']}")
        print(f"  Pass Rate: {oc['pass_rate']}%")

    # Pass/Fail criteria
    print("\n" + "-" * 60)

    # Base quality checks
    base_passed = (
        evaluation['avg_precision'] >= 90 and
        evaluation['avg_recall'] >= 85 and
        evaluation['critical_pass_rate'] >= 95
    )

    # Override compliance check (must be 100% if override cases exist)
    override_passed = True
    if evaluation['override_compliance']:
        override_passed = evaluation['override_compliance']['pass_rate'] == 100.0

    passed = base_passed and override_passed

    if passed:
        print("✅ PASS: Model meets quality thresholds")
    else:
        print("❌ FAIL: Model below quality thresholds")
        if evaluation['avg_precision'] < 90:
            print(f"   - Precision too low ({evaluation['avg_precision']}% < 90%)")
        if evaluation['avg_recall'] < 85:
            print(f"   - Recall too low ({evaluation['avg_recall']}% < 85%)")
        if evaluation['critical_pass_rate'] < 95:
            print(f"   - Critical pass rate too low ({evaluation['critical_pass_rate']}% < 95%)")
        if not override_passed:
            oc = evaluation['override_compliance']
            print(f"   - Override compliance failed ({oc['passed']}/{oc['total_override_cases']} cases passed, requires 100%)")


# ============================================================================
# Main CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Evaluate LLM extraction")
    parser.add_argument("--model", default="mock", help="Model name (mistral, claude-haiku, etc.)")
    parser.add_argument("--test-file", default="tests/fixtures/extraction_test_cases.json",
                        help="Path to test cases JSON")
    parser.add_argument("--runs", type=int, default=1,
                        help="Number of runs per test (for stability check)")
    parser.add_argument("--output", help="Output file for report (optional)")

    args = parser.parse_args()

    # Load test cases
    test_file = PROJECT_ROOT / args.test_file
    test_cases = load_test_cases(test_file)

    if not test_cases:
        print("❌ No test cases loaded")
        return 1

    print(f"Loaded {len(test_cases)} test cases")

    # Initialize extractor
    if args.model == "mock" or IngredientExtractor is None:
        print(f"\nUsing MockExtractor (LLM not available)")
        extractor = MockExtractor()
    else:
        print(f"\nUsing {args.model}")
        extractor = IngredientExtractor(model=args.model)

    # Run evaluation
    evaluation = run_evaluation(
        extractor,
        test_cases,
        model_name=args.model,
        num_runs=args.runs
    )

    # Print summary
    print_summary(evaluation)

    # Save report if requested
    if args.output:
        output_path = PROJECT_ROOT / args.output
        with open(output_path, 'w') as f:
            json.dump(evaluation, f, indent=2)
        print(f"\n📄 Report saved to {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
