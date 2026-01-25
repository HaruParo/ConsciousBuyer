"""Anthropic Claude API client wrapper with error handling and retries."""

import logging
import os
from typing import Optional

from anthropic import Anthropic, APITimeoutError, APIError

logger = logging.getLogger(__name__)

# Opik LLM evaluation and tracing
try:
    from opik import configure as opik_configure
    from opik.integrations.anthropic import track_anthropic
    OPIK_AVAILABLE = True
except ImportError:
    OPIK_AVAILABLE = False
    logger.info("Opik not installed. LLM tracing disabled. Install with: pip install opik")

# Configuration
MODEL = "claude-sonnet-4-20250514"
API_TIMEOUT = 30.0
MAX_RETRIES = 2


def get_anthropic_client() -> Optional[Anthropic]:
    """
    Initialize and return Anthropic client with optional Opik tracing.

    Returns:
        Anthropic client if API key is available, None otherwise.
    """
    # Configure Opik if available
    if OPIK_AVAILABLE:
        try:
            opik_configure()
            logger.info("Opik LLM tracing enabled")
        except Exception as e:
            logger.warning(f"Failed to configure Opik: {e}. Continuing without tracing.")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not found in environment")
        return None

    try:
        client = Anthropic(api_key=api_key)

        # Wrap client with Opik tracking if available
        if OPIK_AVAILABLE:
            try:
                client = track_anthropic(client)
                logger.info("Anthropic client wrapped with Opik tracking")
            except Exception as e:
                logger.warning(f"Failed to enable Opik tracking: {e}. Continuing without tracing.")

        return client
    except Exception as e:
        logger.error(f"Failed to initialize Anthropic client: {e}")
        return None


def call_claude_with_retry(
    client: Anthropic,
    prompt: str,
    max_tokens: int = 1024,
    temperature: float = 0.0,
    max_retries: int = MAX_RETRIES,
) -> Optional[str]:
    """
    Call Claude API with retry logic.

    Args:
        client: Anthropic client instance
        prompt: User prompt to send to Claude
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature (0.0 = deterministic)
        max_retries: Maximum number of retry attempts

    Returns:
        Response text from Claude, or None if all retries failed.
    """
    last_error = None

    for attempt in range(max_retries):
        try:
            logger.debug(f"Claude API call attempt {attempt + 1}/{max_retries}")

            response = client.messages.create(
                model=MODEL,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=API_TIMEOUT,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract text from response blocks
            response_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    response_text += block.text

            logger.debug(f"Claude response received: {len(response_text)} chars")
            return response_text

        except APITimeoutError as e:
            logger.warning(f"API timeout on attempt {attempt + 1}: {e}")
            last_error = f"Timeout: {e}"

        except APIError as e:
            logger.warning(f"API error on attempt {attempt + 1}: {e}")
            last_error = f"API error: {e}"

        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            last_error = f"Unexpected error: {e}"

    logger.error(f"All {max_retries} Claude API attempts failed. Last error: {last_error}")
    return None
