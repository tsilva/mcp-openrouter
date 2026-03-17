"""OpenRouter API client."""

import base64
import sys
import time
from pathlib import Path

import requests


class OpenRouterClient:
    """Client for the OpenRouter API."""

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_key: str):
        """Initialize the client with an API key.

        Args:
            api_key: OpenRouter API key from https://openrouter.ai/keys
        """
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://claude.ai/claude-code",
            "X-Title": "Claude Code MCP",
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        payload: dict | None = None,
        *,
        params: dict | None = None,
        max_retries: int = 3,
    ):
        """Make API request with retry logic."""
        url = endpoint if endpoint.startswith("http") else f"{self.BASE_URL}/{endpoint}"

        for attempt in range(max_retries):
            try:
                if method == "GET":
                    response = requests.get(
                        url,
                        headers=self.headers,
                        params=params,
                        timeout=120,
                    )
                else:
                    response = requests.post(
                        url, headers=self.headers, json=payload, timeout=120
                    )

                if response.status_code == 200:
                    return response.json()

                code, message = self._parse_error_response(response)

                # Retryable errors
                if code in [408, 429, 502, 503] and attempt < max_retries - 1:
                    wait = min(2**attempt * 2, 30)
                    print(
                        f"Retrying in {wait}s (attempt {attempt + 1}/{max_retries})...",
                        file=sys.stderr,
                    )
                    time.sleep(wait)
                    continue

                # Non-retryable errors
                error_messages = {
                    400: "Bad request - check parameters",
                    401: "Invalid API key - check OPENROUTER_API_KEY",
                    402: "Insufficient credits - add funds at openrouter.ai",
                    403: "Content flagged by moderation",
                    429: "Rate limited - wait before retrying",
                }
                msg = error_messages.get(code, message)
                raise Exception(f"OpenRouter error {code}: {msg}")

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    continue
                raise Exception("Request timed out after retries")
            except requests.exceptions.RequestException as e:
                raise Exception(f"Network error: {e}")

        raise Exception("Max retries exceeded")

    @staticmethod
    def _parse_error_response(response) -> tuple[int, str]:
        """Extract an error code and message from JSON or plain-text responses."""
        try:
            payload = response.json()
        except ValueError:
            return response.status_code, response.text

        error = payload.get("error", {})
        code = error.get("code", response.status_code)
        message = error.get("message") or payload.get("message") or response.text
        return code, message

    def chat(self, model: str, messages: list, **kwargs) -> dict:
        """Send chat completion request.

        Args:
            model: Model identifier (e.g., "anthropic/claude-sonnet-4")
            messages: List of message dicts with 'role' and 'content' keys
            **kwargs: Additional parameters (max_tokens, temperature, etc.)

        Returns:
            Full API response dict
        """
        payload = {"model": model, "messages": messages}
        payload.update(kwargs)
        return self._request("POST", "chat/completions", payload)

    def chat_simple(self, model: str, prompt: str, system: str = None, **kwargs) -> str:
        """Simple chat - returns just the response text.

        Args:
            model: Model identifier (e.g., "anthropic/claude-sonnet-4")
            prompt: User message to send
            system: Optional system prompt
            **kwargs: Additional parameters (max_tokens, temperature, etc.)

        Returns:
            Response text content
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        result = self.chat(model, messages, **kwargs)
        return result["choices"][0]["message"]["content"]

    def generate_image(
        self,
        model: str,
        prompt: str,
        output_path: str = None,
        aspect_ratio: str = "1:1",
        size: str = "1K",
        background: str = None,
        quality: str = None,
        output_format: str = None,
    ) -> list:
        """Generate image using chat completions endpoint.

        Args:
            model: Image model (e.g., "google/gemini-3-pro-image-preview")
            prompt: Image description
            output_path: Absolute path to save the image (optional)
            aspect_ratio: Aspect ratio (1:1, 16:9, 9:16, 4:3, 3:4, 21:9)
            size: Image size (1K, 2K, 4K)
            background: Background setting (e.g., "transparent")
            quality: Quality setting (e.g., "high", "medium", "low")
            output_format: Output format (e.g., "png", "webp", "jpeg")

        Returns:
            List of generated images with image_url data
        """
        image_config = {"aspect_ratio": aspect_ratio, "image_size": size}

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "modalities": ["image", "text"],
            "image_config": image_config,
            "n": 1,
        }

        # Add top-level parameters (for OpenAI GPT Image models)
        if background:
            payload["background"] = background
        if quality:
            payload["quality"] = quality
        if output_format:
            payload["output_format"] = output_format

        result = self._request("POST", "chat/completions", payload)
        images = result["choices"][0]["message"].get("images", [])

        if output_path and images:
            output = Path(output_path).resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            for idx, img in enumerate(images):
                data_url = img["image_url"]["url"]
                base64_data = data_url.split(",")[1]
                if len(images) == 1:
                    path = output
                else:
                    path = output.parent / f"{output.stem}_{idx}{output.suffix}"
                with open(path, "wb") as f:
                    f.write(base64.b64decode(base64_data))

        return images

    @staticmethod
    def _model_identifier(model: dict) -> str | None:
        """Return the public identifier for a model."""
        return model.get("id") or model.get("slug") or model.get("canonical_slug")

    @staticmethod
    def _input_modalities(model: dict) -> list[str]:
        """Return normalized input modalities."""
        architecture = model.get("architecture") or {}
        return list(
            model.get("input_modalities")
            or architecture.get("input_modalities")
            or []
        )

    @staticmethod
    def _output_modalities(model: dict) -> list[str]:
        """Return normalized output modalities."""
        architecture = model.get("architecture") or {}
        return list(
            model.get("output_modalities")
            or architecture.get("output_modalities")
            or []
        )

    @classmethod
    def _normalize_model(cls, model: dict) -> dict | None:
        """Normalize model records from the public models API."""
        slug = cls._model_identifier(model)
        if not slug:
            return None

        return {
            "slug": slug,
            "name": model.get("name", slug),
            "context_length": model.get("context_length"),
            "pricing": dict(model.get("pricing") or {}),
            "supported_parameters": list(model.get("supported_parameters") or []),
            "input_modalities": cls._input_modalities(model),
            "output_modalities": cls._output_modalities(model),
        }

    def _fetch_models(self, output_modality: str | None = None) -> list[dict]:
        """Fetch and normalize models from the public OpenRouter API."""
        params = {"output_modalities": output_modality} if output_modality else None
        result = self._request("GET", "models", params=params)
        models = result.get("data", [])
        normalized: list[dict] = []
        for model in models:
            item = self._normalize_model(model)
            if item is not None:
                normalized.append(item)
        return normalized

    @staticmethod
    def _filter_models(models: list[dict], capability: str | None) -> list[dict]:
        """Filter normalized models by capability."""
        if capability == "vision":
            return [m for m in models if "image" in m.get("input_modalities", [])]
        if capability == "image_gen":
            return [m for m in models if "image" in m.get("output_modalities", [])]
        if capability == "embedding":
            return [m for m in models if "embeddings" in m.get("output_modalities", [])]
        if capability == "tools":
            return [m for m in models if "tools" in m.get("supported_parameters", [])]
        if capability == "long_context":
            return [m for m in models if m.get("context_length", 0) >= 100000]
        return models

    def list_models(self, capability: str = None) -> list:
        """List available models, optionally filtered by capability.

        Args:
            capability: Filter by capability (vision, image_gen, tools, long_context)

        Returns:
            List of model dicts with slug, name, context_length, pricing, etc.
        """
        if capability == "image_gen":
            return self._filter_models(self._fetch_models("image"), capability)
        if capability == "embedding":
            return self._filter_models(self._fetch_models("embeddings"), capability)

        merged: dict[str, dict] = {}
        for modality in (None, "image", "embeddings"):
            for model in self._fetch_models(modality):
                merged.setdefault(model["slug"], model)

        return self._filter_models(list(merged.values()), capability)

    def embeddings(self, model: str, input: str | list[str], **kwargs) -> dict:
        """Generate embeddings for text input.

        Args:
            model: Embedding model identifier (e.g., "mistralai/mistral-embed-2312")
            input: Text string or list of strings to embed
            **kwargs: Additional parameters (encoding_format, dimensions)

        Returns:
            Full API response dict
        """
        payload = {"model": model, "input": input}
        payload.update(kwargs)
        return self._request("POST", "embeddings", payload)

    def find_model(self, search_term: str) -> list:
        """Find models matching search term.

        Args:
            search_term: Text to search for in model names/slugs

        Returns:
            List of matching model dicts
        """
        models = self.list_models()
        search_lower = search_term.lower()
        return [
            m
            for m in models
            if search_lower in m["slug"].lower() or search_lower in m["name"].lower()
        ]
