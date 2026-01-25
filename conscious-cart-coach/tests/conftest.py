"""Pytest configuration with Opik integration for LLM test tracking."""

import os
import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"\n✅ Loaded environment from {env_path}")
    else:
        print(f"\n⚠️  No .env file found at {env_path}")
except ImportError:
    print("\n⚠️  python-dotenv not installed. Install with: pip install python-dotenv")

# Check if Opik is available
try:
    from opik.integrations.pytest import OpikPytestPlugin
    OPIK_AVAILABLE = True
except ImportError:
    OPIK_AVAILABLE = False


def pytest_configure(config):
    """Configure pytest with Opik plugin if available."""
    if OPIK_AVAILABLE and os.getenv("OPIK_API_KEY"):
        # Register Opik plugin for test tracking
        config.pluginmanager.register(OpikPytestPlugin(), "opik_pytest")
        print("\n✅ Opik test tracking enabled")
    else:
        if not OPIK_AVAILABLE:
            print("\n⚠️  Opik not installed. Test tracking disabled. Install with: pip install opik")
        elif not os.getenv("OPIK_API_KEY"):
            print("\n⚠️  OPIK_API_KEY not found. Test tracking disabled.")


@pytest.fixture(scope="session")
def anthropic_client():
    """
    Provide Anthropic client for LLM tests.

    Tests using this fixture will be skipped if ANTHROPIC_API_KEY is not set.
    """
    from src.llm.client import get_anthropic_client

    client = get_anthropic_client()
    if not client:
        pytest.skip("ANTHROPIC_API_KEY not found. Skipping LLM tests.")

    return client


@pytest.fixture(scope="session")
def skip_if_no_api_key():
    """Skip test if ANTHROPIC_API_KEY is not configured."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not found. Skipping LLM tests.")
