"""Anthropic Claude API client wrapper with error handling and retries."""

import logging
import os
from typing import Optional

from anthropic import Anthropic, APITimeoutError, APIError

logger = logging.getLogger(__name__)

# Opik LLM evaluation and tracing
try:
    from opik import configure as opik_configure, track
    from opik.integrations.anthropic import track_anthropic
    import opik
    OPIK_AVAILABLE = True
except ImportError:
    OPIK_AVAILABLE = False
    opik = None
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
            # Get Opik configuration from environment
            opik_api_key = os.getenv("OPIK_API_KEY")
            opik_workspace = os.getenv("OPIK_WORKSPACE")
            opik_project = os.getenv("OPIK_PROJECT_NAME", "consciousbuyer")

            # Configure Opik with project name
            config_kwargs = {}
            if opik_api_key:
                config_kwargs["api_key"] = opik_api_key
            if opik_workspace:
                config_kwargs["workspace"] = opik_workspace

            opik_configure(**config_kwargs)

            # Set project name for all traces
            if opik and hasattr(opik, 'configure_project'):
                opik.configure_project(project_name=opik_project)

            logger.info(f"Opik LLM tracing enabled (project: {opik_project})")
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
                client = track_anthropic(client, project_name=os.getenv("OPIK_PROJECT_NAME", "consciousbuyer"))
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
    trace_name: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> Optional[str]:
    """
    Call Claude API with retry logic and Opik tracing.

    Args:
        client: Anthropic client instance
        prompt: User prompt to send to Claude
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature (0.0 = deterministic)
        max_retries: Maximum number of retry attempts
        trace_name: Optional name for Opik trace (e.g., "ingredient_extraction")
        metadata: Optional metadata dict to attach to trace

    Returns:
        Response text from Claude, or None if all retries failed.
    """
    last_error = None

    # Create Opik trace context if available
    trace_context = {}
    if OPIK_AVAILABLE and trace_name:
        trace_context = {
            "name": trace_name,
            "metadata": metadata or {},
            "tags": ["anthropic", "claude", os.getenv("OPIK_PROJECT_NAME", "consciousbuyer")]
        }

    for attempt in range(max_retries):
        try:
            logger.debug(f"Claude API call attempt {attempt + 1}/{max_retries}")

            # Track retry attempts in metadata
            if trace_context and attempt > 0:
                trace_context["metadata"]["retry_attempt"] = attempt

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

            # Log success to Opik trace
            if trace_context:
                trace_context["metadata"]["status"] = "success"
                trace_context["metadata"]["total_attempts"] = attempt + 1

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

    # Log failure to Opik trace
    if trace_context:
        trace_context["metadata"]["status"] = "failed"
        trace_context["metadata"]["total_attempts"] = max_retries
        trace_context["metadata"]["last_error"] = last_error

    logger.error(f"All {max_retries} Claude API attempts failed. Last error: {last_error}")
    return None
