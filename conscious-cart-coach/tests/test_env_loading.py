"""
Quick test to verify environment variables are loading correctly.

Run: python -m pytest tests/test_env_loading.py -v -s
"""

import os
import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_env_file_exists():
    """Verify .env file exists."""
    env_path = Path(__file__).parent.parent / ".env"
    assert env_path.exists(), f".env file not found at {env_path}"
    print(f"\n✅ .env file exists at: {env_path}")


def test_anthropic_api_key_loaded():
    """Verify ANTHROPIC_API_KEY is loaded from environment."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    assert api_key is not None, "ANTHROPIC_API_KEY not found in environment"
    assert api_key.startswith("sk-ant-"), f"Invalid ANTHROPIC_API_KEY format: {api_key[:10]}..."
    print(f"\n✅ ANTHROPIC_API_KEY loaded: {api_key[:15]}...")


def test_opik_api_key_loaded():
    """Verify OPIK_API_KEY is loaded (optional)."""
    api_key = os.getenv("OPIK_API_KEY")
    if api_key:
        print(f"\n✅ OPIK_API_KEY loaded: {api_key[:10]}...")
    else:
        print("\n⚠️  OPIK_API_KEY not set (optional)")


def test_opik_workspace_loaded():
    """Verify OPIK_WORKSPACE is loaded (optional)."""
    workspace = os.getenv("OPIK_WORKSPACE")
    if workspace:
        print(f"\n✅ OPIK_WORKSPACE loaded: {workspace}")
    else:
        print("\n⚠️  OPIK_WORKSPACE not set (optional)")


def test_opik_project_name_loaded():
    """Verify OPIK_PROJECT_NAME is loaded."""
    project_name = os.getenv("OPIK_PROJECT_NAME")
    if project_name:
        print(f"\n✅ OPIK_PROJECT_NAME loaded: {project_name}")
    else:
        print("\n⚠️  OPIK_PROJECT_NAME not set (will default to 'consciousbuyer')")


def test_can_import_llm_client():
    """Verify we can import the LLM client."""
    try:
        from src.llm.client import get_anthropic_client
        print("\n✅ Successfully imported get_anthropic_client")
    except ImportError as e:
        pytest.fail(f"Failed to import LLM client: {e}")


def test_can_initialize_anthropic_client():
    """Verify we can initialize Anthropic client."""
    from src.llm.client import get_anthropic_client

    client = get_anthropic_client()
    assert client is not None, "Failed to initialize Anthropic client (check API key)"
    print("\n✅ Successfully initialized Anthropic client")


def test_opik_available():
    """Check if Opik is installed and available."""
    try:
        import opik
        print(f"\n✅ Opik installed (version: {opik.__version__ if hasattr(opik, '__version__') else 'unknown'})")
    except ImportError:
        print("\n⚠️  Opik not installed. Install with: pip install opik>=0.1.0")


def test_summary():
    """Print summary of environment configuration."""
    print("\n" + "="*60)
    print("ENVIRONMENT CONFIGURATION SUMMARY")
    print("="*60)

    # Check each variable
    checks = {
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "OPIK_API_KEY": os.getenv("OPIK_API_KEY"),
        "OPIK_WORKSPACE": os.getenv("OPIK_WORKSPACE"),
        "OPIK_PROJECT_NAME": os.getenv("OPIK_PROJECT_NAME", "consciousbuyer"),
    }

    for key, value in checks.items():
        if value:
            if "KEY" in key:
                print(f"✅ {key}: {value[:15]}...")
            else:
                print(f"✅ {key}: {value}")
        else:
            required = key == "ANTHROPIC_API_KEY"
            symbol = "❌" if required else "⚠️ "
            status = "REQUIRED" if required else "optional"
            print(f"{symbol} {key}: not set ({status})")

    print("="*60)

    # Check if ready for LLM tests
    if checks["ANTHROPIC_API_KEY"]:
        print("\n✅ Ready to run LLM tests!")
        print("   Run: pytest -m llm")
    else:
        print("\n❌ Cannot run LLM tests - ANTHROPIC_API_KEY missing")
        print("   Fix: Add ANTHROPIC_API_KEY to .env file")

    if checks["OPIK_API_KEY"]:
        print("\n✅ Ready for Opik tracking!")
        print("   Traces will appear in Opik dashboard")
    else:
        print("\n⚠️  Opik tracking disabled (OPIK_API_KEY not set)")
        print("   Tests will run but won't log to Opik dashboard")

    print("")
