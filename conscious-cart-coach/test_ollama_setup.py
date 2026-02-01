#!/usr/bin/env python3
"""
Test LLM Provider Setup for Conscious Cart Coach

This script tests:
1. LLM provider is configured
2. Provider is accessible
3. LLM client can generate responses
4. Ingredient extraction works

Supports: Ollama, Anthropic, Gemini, OpenAI
"""

import os
import sys
import requests
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.llm_client import get_llm_client, OllamaClient


def check_ollama_server():
    """Check if Ollama server is running"""
    print("1. Checking Ollama server...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("   ✅ Ollama server is running")
            return True
        else:
            print(f"   ❌ Ollama server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   ❌ Ollama server is not running")
        print("      Start it with: ollama serve")
        return False
    except Exception as e:
        print(f"   ❌ Error checking Ollama: {e}")
        return False


def check_model_available(model_name="mistral"):
    """Check if the specified model is available"""
    print(f"\n2. Checking if model '{model_name}' is available...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]

            if any(model_name in name for name in model_names):
                print(f"   ✅ Model '{model_name}' is available")
                return True
            else:
                print(f"   ❌ Model '{model_name}' not found")
                print(f"      Available models: {', '.join(model_names) if model_names else 'None'}")
                print(f"      Pull it with: ollama pull {model_name}")
                return False
    except Exception as e:
        print(f"   ❌ Error checking models: {e}")
        return False


def test_simple_generation():
    """Test simple text generation"""
    print("\n3. Testing simple text generation...")
    try:
        client = OllamaClient(model=os.environ.get("OLLAMA_MODEL", "mistral"))

        response = client.generate_sync(
            prompt="Say hello and confirm you are working correctly.",
            temperature=0.7,
            max_tokens=100,
        )

        print(f"   ✅ Generation successful")
        print(f"      Response: {response.text[:100]}...")
        print(f"      Tokens: {response.usage}")
        return True

    except Exception as e:
        print(f"   ❌ Generation failed: {e}")
        return False


def test_ingredient_extraction():
    """Test ingredient extraction for Conscious Cart Coach"""
    print("\n4. Testing ingredient extraction...")
    try:
        client = get_llm_client(provider="ollama")

        prompt = """Extract ingredients from this meal plan: chicken biryani for 4 people

Return as a JSON array with this format:
[
  {"name": "chicken", "amount": 1.5, "unit": "lb"},
  {"name": "basmati rice", "amount": 2, "unit": "cups"},
  ...
]

Only return the JSON array, nothing else."""

        response = client.generate_sync(
            prompt=prompt,
            system="You are a grocery shopping assistant that extracts ingredients from meal descriptions.",
            temperature=0.5,
            max_tokens=500,
        )

        print(f"   ✅ Ingredient extraction successful")
        print(f"      Response:\n{response.text[:300]}...")
        print(f"      Tokens: {response.usage}")
        return True

    except Exception as e:
        print(f"   ❌ Extraction failed: {e}")
        return False


def test_env_configuration():
    """Test .env configuration"""
    print("\n5. Checking .env configuration...")

    llm_provider = os.environ.get("LLM_PROVIDER", "not set")
    ollama_base_url = os.environ.get("OLLAMA_BASE_URL", "not set")
    ollama_model = os.environ.get("OLLAMA_MODEL", "not set")

    print(f"   LLM_PROVIDER: {llm_provider}")
    print(f"   OLLAMA_BASE_URL: {ollama_base_url}")
    print(f"   OLLAMA_MODEL: {ollama_model}")

    if llm_provider == "ollama":
        print("   ✅ LLM_PROVIDER set to ollama")
        return True
    else:
        print(f"   ⚠️  LLM_PROVIDER is '{llm_provider}', expected 'ollama'")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Ollama Setup Test for Conscious Cart Coach")
    print("=" * 60)

    # Load .env if python-dotenv is available
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded .env file\n")
    except ImportError:
        print("⚠️  python-dotenv not installed, .env not loaded")
        print("   Install with: pip install python-dotenv\n")

    results = []

    # Run all tests
    results.append(("Ollama Server", check_ollama_server()))
    results.append(("Model Available", check_model_available(os.environ.get("OLLAMA_MODEL", "mistral"))))
    results.append(("Simple Generation", test_simple_generation()))
    results.append(("Ingredient Extraction", test_ingredient_extraction()))
    results.append(("ENV Configuration", test_env_configuration()))

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("\n🎉 All tests passed! Ollama is ready to use.")
        print("\nNext steps:")
        print("  1. Your agents will now use Ollama instead of Anthropic")
        print("  2. Test cart creation: http://localhost:5173")
        print("  3. Check backend logs for LLM calls")
    else:
        print("\n⚠️  Some tests failed. Fix the issues above before using Ollama.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
