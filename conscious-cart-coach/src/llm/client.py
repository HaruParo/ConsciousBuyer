"""
Unified LLM client wrapper with support for Anthropic and Ollama.

This module provides backward compatibility with the existing Anthropic-based
codebase while adding support for Ollama (local LLMs).

The client automatically switches between providers based on LLM_PROVIDER env variable.
"""

import logging
import os
from typing import Optional

# Keep Anthropic import for type hints and backward compatibility
try:
    from anthropic import Anthropic, APITimeoutError, APIError
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    Anthropic = None
    APITimeoutError = Exception
    APIError = Exception

logger = logging.getLogger(__name__)

# Import the unified LLM client
from ..utils.llm_client import get_llm_client, BaseLLMClient, AnthropicClient, OllamaClient, GeminiClient, OpenAIClient

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


def get_anthropic_client() -> Optional[BaseLLMClient]:
    """
    Initialize and return LLM client (Anthropic or Ollama) based on configuration.

    Now returns a unified LLM client that can be Anthropic or Ollama based on
    LLM_PROVIDER environment variable.

    Returns:
        Unified LLM client (BaseLLMClient), or None if initialization fails.

    Note:
        This function maintains backward compatibility but now returns a unified
        client instead of a raw Anthropic client. The interface is compatible.
    """
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    logger.info(f"Initializing LLM client with provider: {provider}")

    # Configure Opik if available (for Anthropic only currently)
    if OPIK_AVAILABLE and provider == "anthropic":
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

    try:
        # Get unified client based on provider
        client = get_llm_client(provider=provider)

        # Wrap Anthropic client with Opik tracking if available
        if OPIK_AVAILABLE and isinstance(client, AnthropicClient) and client.client:
            try:
                client.client = track_anthropic(
                    client.client,
                    project_name=os.getenv("OPIK_PROJECT_NAME", "consciousbuyer")
                )
                logger.info("Anthropic client wrapped with Opik tracking")
            except Exception as e:
                logger.warning(f"Failed to enable Opik tracking: {e}. Continuing without tracing.")

        logger.info(f"LLM client initialized successfully: {client.__class__.__name__}")
        return client

    except Exception as e:
        logger.error(f"Failed to initialize LLM client: {e}")
        logger.warning("Returning None - LLM features will be disabled")
        return None


def call_claude_with_retry(
    client: BaseLLMClient,
    prompt: str,
    max_tokens: int = 1024,
    temperature: float = 0.0,
    max_retries: int = MAX_RETRIES,
    trace_name: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> Optional[str]:
    """
    Call LLM API (Anthropic or Ollama) with retry logic and Opik tracing.

    This function now works with both Anthropic and Ollama clients.

    Args:
        client: LLM client instance (AnthropicClient or OllamaClient)
        prompt: User prompt to send to LLM
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature (0.0 = deterministic)
        max_retries: Maximum number of retry attempts
        trace_name: Optional name for Opik trace (e.g., "ingredient_extraction")
        metadata: Optional metadata dict to attach to trace

    Returns:
        Response text from LLM, or None if all retries failed.
    """
    if not client:
        logger.error("No LLM client available")
        return None

    last_error = None
    provider_name = client.__class__.__name__

    # Create Opik trace context if available
    trace_context = {}
    if OPIK_AVAILABLE and trace_name:
        trace_context = {
            "name": trace_name,
            "metadata": metadata or {},
            "tags": [provider_name.lower(), os.getenv("OPIK_PROJECT_NAME", "consciousbuyer")]
        }

    for attempt in range(max_retries):
        try:
            logger.debug(f"{provider_name} API call attempt {attempt + 1}/{max_retries}")

            # Track retry attempts in metadata
            if trace_context and attempt > 0:
                trace_context["metadata"]["retry_attempt"] = attempt

            # Call the unified client
            response = client.generate_sync(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            response_text = response.text
            logger.debug(f"{provider_name} response received: {len(response_text)} chars")
            logger.debug(f"Token usage: {response.usage}")

            # Log success to Opik trace
            if trace_context:
                trace_context["metadata"]["status"] = "success"
                trace_context["metadata"]["total_attempts"] = attempt + 1
                trace_context["metadata"]["token_usage"] = response.usage

            return response_text

        except ConnectionError as e:
            logger.warning(f"Connection error on attempt {attempt + 1}: {e}")
            last_error = f"Connection error: {e}"
            if isinstance(client, OllamaClient):
                logger.warning("Make sure Ollama is running: ollama serve")

        except TimeoutError as e:
            logger.warning(f"Timeout on attempt {attempt + 1}: {e}")
            last_error = f"Timeout: {e}"

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

    logger.error(f"All {max_retries} {provider_name} API attempts failed. Last error: {last_error}")
    return None
