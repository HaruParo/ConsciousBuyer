"""
Unified LLM Client for Conscious Cart Coach

Supports multiple LLM providers:
- Anthropic (Claude via API)
- Ollama (Local models)
- OpenAI (GPT models)

Usage:
    from src.utils.llm_client import get_llm_client

    client = get_llm_client()
    response = await client.generate(
        prompt="Extract ingredients from: chicken biryani for 4",
        system="You are a grocery shopping assistant"
    )
"""

import os
import json
import requests
from typing import Optional, Dict, Any, List

# Make anthropic import optional (only needed for Anthropic provider)
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    Anthropic = None
    ANTHROPIC_AVAILABLE = False


class LLMResponse:
    """Standardized response format across all LLM providers"""

    def __init__(self, text: str, usage: Optional[Dict] = None, raw_response: Optional[Any] = None):
        self.text = text
        self.usage = usage or {}
        self.raw_response = raw_response


class BaseLLMClient:
    """Base class for all LLM clients"""

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        raise NotImplementedError

    def generate_sync(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Synchronous version for backwards compatibility"""
        raise NotImplementedError


class AnthropicClient(BaseLLMClient):
    """Anthropic (Claude) API client"""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-haiku-20240307"):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic package not installed. Install with: pip install anthropic")

        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
        self.client = Anthropic(api_key=self.api_key) if self.api_key else None

        if not self.client:
            raise ValueError("ANTHROPIC_API_KEY not set")

    def generate_sync(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        use_cache: bool = True,
    ) -> LLMResponse:
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # Enable prompt caching for system prompt (reduces cost on repeated calls)
        # See: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
        if system:
            if use_cache:
                kwargs["system"] = [
                    {
                        "type": "text",
                        "text": system,
                        "cache_control": {"type": "ephemeral"}
                    }
                ]
            else:
                kwargs["system"] = system

        response = self.client.messages.create(**kwargs)

        return LLMResponse(
            text=response.content[0].text,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            raw_response=response,
        )

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        # For now, just call sync version
        # TODO: Use async Anthropic client when needed
        return self.generate_sync(prompt, system, temperature, max_tokens)


class OllamaClient(BaseLLMClient):
    """Ollama (Local LLM) client"""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "mistral",
    ):
        self.base_url = base_url
        self.model = model
        self.api_url = f"{base_url}/api/generate"

    def generate_sync(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        # Combine system prompt with user prompt for Ollama
        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            response = requests.post(self.api_url, json=payload, timeout=180)
            response.raise_for_status()
            result = response.json()

            return LLMResponse(
                text=result.get("response", ""),
                usage={
                    "input_tokens": result.get("prompt_eval_count", 0),
                    "output_tokens": result.get("eval_count", 0),
                },
                raw_response=result,
            )

        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Could not connect to Ollama at {self.base_url}. "
                f"Make sure Ollama is running with: ollama serve"
            )
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Ollama request timed out after 180 seconds")
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        # For now, just call sync version
        # TODO: Use aiohttp for true async when needed
        return self.generate_sync(prompt, system, temperature, max_tokens)


class GeminiClient(BaseLLMClient):
    """Google Gemini API client"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-1.5-flash",
    ):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.model = model
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models"

        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not set")

    def generate_sync(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        import requests

        # Build the request
        url = f"{self.api_url}/{self.model}:generateContent?key={self.api_key}"

        # Combine system and user prompts
        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": full_prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }

        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()

            # Extract text from Gemini response
            text = ""
            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    for part in candidate["content"]["parts"]:
                        if "text" in part:
                            text += part["text"]

            # Extract token usage
            usage = {}
            if "usageMetadata" in result:
                metadata = result["usageMetadata"]
                usage = {
                    "input_tokens": metadata.get("promptTokenCount", 0),
                    "output_tokens": metadata.get("candidatesTokenCount", 0),
                }

            return LLMResponse(
                text=text,
                usage=usage,
                raw_response=result,
            )

        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                "Could not connect to Google Gemini API. Check your internet connection."
            )
        except requests.exceptions.Timeout:
            raise TimeoutError("Gemini API request timed out after 60 seconds")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                raise ValueError(f"Invalid request to Gemini API: {e.response.text}")
            elif e.response.status_code == 401:
                raise ValueError("Invalid GOOGLE_API_KEY. Check your API key.")
            elif e.response.status_code == 429:
                raise Exception("Gemini API rate limit exceeded. Try again later.")
            else:
                raise Exception(f"Gemini API error ({e.response.status_code}): {e.response.text}")
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        # For now, just call sync version
        # TODO: Use aiohttp for true async when needed
        return self.generate_sync(prompt, system, temperature, max_tokens)


class OpenAIClient(BaseLLMClient):
    """OpenAI (GPT) API client"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")

        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "OpenAI package not installed. Install with: pip install openai"
            )

    def generate_sync(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        messages = []

        if system:
            messages.append({"role": "system", "content": system})

        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            text = response.choices[0].message.content

            usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            }

            return LLMResponse(
                text=text,
                usage=usage,
                raw_response=response,
            )

        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        # For now, just call sync version
        # TODO: Use async OpenAI client when needed
        return self.generate_sync(prompt, system, temperature, max_tokens)


def get_llm_client(provider: Optional[str] = None) -> BaseLLMClient:
    """
    Factory function to get the appropriate LLM client based on configuration

    Args:
        provider: Override provider ("anthropic", "ollama", "gemini", "openai")
                 If None, uses LLM_PROVIDER from .env

    Returns:
        Configured LLM client instance

    Raises:
        ValueError: If provider is invalid or required credentials missing
    """
    # Default to anthropic on Vercel/serverless, ollama for local development
    is_serverless = os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
    default_provider = "anthropic" if is_serverless else "ollama"
    provider = provider or os.environ.get("LLM_PROVIDER", default_provider).lower()

    if provider == "anthropic":
        client = AnthropicClient(
            model=os.environ.get("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
        )

        # Wrap with Opik tracking if available
        try:
            import opik
            from opik.integrations.anthropic import track_anthropic

            # Configure Opik with API key if available
            opik_api_key = os.environ.get("OPIK_API_KEY")
            opik_workspace = os.environ.get("OPIK_WORKSPACE")
            opik_project = os.environ.get("OPIK_PROJECT_NAME", "consciousbuyer")

            if opik_api_key:
                opik.configure(
                    api_key=opik_api_key,
                    workspace=opik_workspace if opik_workspace else None
                )

            if client.client:
                client.client = track_anthropic(
                    client.client,
                    project_name=opik_project
                )
                print(f"[Opik] Anthropic client wrapped with tracking (project: {opik_project})")
        except ImportError:
            pass  # Opik not installed
        except Exception as e:
            print(f"[Opik] Failed to enable tracking: {e}")

        return client

    elif provider == "ollama":
        return OllamaClient(
            base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
            model=os.environ.get("OLLAMA_MODEL", "gpt-oss:20b"),
        )

    elif provider == "gemini":
        return GeminiClient(
            model=os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
        )

    elif provider == "openai":
        return OpenAIClient(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        )

    else:
        raise ValueError(
            f"Unknown LLM provider: {provider}. "
            f"Valid options: anthropic, ollama, gemini, openai"
        )


# Convenience function for quick testing
def test_llm_client():
    """Test the configured LLM client"""
    client = get_llm_client()

    print(f"Testing {client.__class__.__name__}...")

    response = client.generate_sync(
        prompt="Extract ingredients from: chicken biryani for 4 people",
        system="You are a grocery shopping assistant. Extract ingredients as a simple list.",
        temperature=0.7,
    )

    print(f"\nResponse:\n{response.text}")
    print(f"\nUsage: {response.usage}")


if __name__ == "__main__":
    test_llm_client()
