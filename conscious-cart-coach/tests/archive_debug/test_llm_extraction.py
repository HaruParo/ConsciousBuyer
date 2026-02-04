#!/usr/bin/env python3
"""Test LLM extraction directly."""
import os
import sys

# Set environment
os.environ['LLM_PROVIDER'] = 'ollama'
os.environ['OLLAMA_MODEL'] = 'mistral:latest'
os.environ['OLLAMA_BASE_URL'] = 'http://localhost:11434'

# Add project to path
sys.path.insert(0, '/Users/hash/Documents/ConsciousBuyer/conscious-cart-coach')

try:
    # Import OllamaClient directly
    from src.utils.llm_client import OllamaClient

    print("Creating Ollama client...")
    client = OllamaClient(
        base_url='http://localhost:11434',
        model='mistral:latest'
    )

    # Test prompt
    from src.llm.ingredient_extractor import INGREDIENT_EXTRACTION_PROMPT

    prompt = INGREDIENT_EXTRACTION_PROMPT.format(
        prompt="chicken biryani for 4",
        servings=4
    )

    print(f"Sending prompt to Mistral (length: {len(prompt)} chars)...")
    print(f"\nPrompt preview:\n{prompt[:500]}...\n")

    response = client.generate_sync(
        prompt=prompt,
        temperature=0.0,
        max_tokens=2048
    )

    print(f"✓ Response received ({len(response.text)} chars)")
    print(f"\nResponse:\n{response.text}\n")

    # Try to parse
    import json
    try:
        data = json.loads(response.text.strip())
        ingredients = data.get('ingredients', [])
        print(f"\n✓ Parsed {len(ingredients)} ingredients:")
        for ing in ingredients:
            print(f"  - {ing.get('name')}")
    except json.JSONDecodeError as e:
        print(f"\n✗ JSON parse error: {e}")
        print(f"Attempting to extract JSON...")
        import re
        json_match = re.search(r'\{[^{}]*"ingredients"[\s\S]*?\}(?=\s*$)', response.text, re.DOTALL)
        if json_match:
            print(f"Found JSON pattern, trying again...")
            try:
                data = json.loads(json_match.group(0))
                ingredients = data.get('ingredients', [])
                print(f"✓ Parsed {len(ingredients)} ingredients")
            except:
                print("Still failed to parse")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
