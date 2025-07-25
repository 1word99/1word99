import logging
import time
from enum import Enum, auto
from typing import Any, AsyncGenerator, Dict, Optional

import backoff
import httpx
from pydantic import BaseModel, validator

from osmanli_ai.plugins.base import (
    BasePlugin,
    ComponentStatus,
    PluginMetadata,
    PluginType,
)

logger = logging.getLogger(__name__)


class LLMBackend(Enum):
    """Enhanced LLM backend types with automatic value assignment"""

    HUGGINGFACE_LOCAL = auto()
    HUGGINGFACE_API = auto()
    OPENAI = auto()
    ANTHROPIC = auto()
    GEMINI = auto()
    MISTRAL = auto()
    LLAMA_CPP = auto()


class ModelConfig(BaseModel):
    """Structured configuration using Pydantic for validation"""

    model_name: str
    backend: LLMBackend
    api_key: Optional[str] = None
    device: str = "auto"
    quantize: bool = False
    temperature: float = 0.7
    max_tokens: int = 512
    timeout: int = 30
    system_prompt: str = "You are a helpful AI assistant."

    @validator("temperature")
    def validate_temperature(cls, v):
        if not 0 <= v <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        return v


class GenerationResult(BaseModel):
    """Structured output from LLM generation"""

    text: str
    tokens_used: int
    finish_reason: str
    processing_time: float


# This is the actual plugin class that inherits from BasePlugin
class GeneralLLMPlugin(BasePlugin):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model_config: Optional[ModelConfig] = None
        self.http_client: Optional[httpx.AsyncClient] = None
        self._load_model_config()

    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        """Returns the metadata for the General LLM plugin."""
        return PluginMetadata(
            name="GeneralLLMPlugin",
            version="0.1.0",
            author="Osmanli AI",
            description="Provides general language model capabilities via various backends.",
            plugin_type=PluginType.LLM,
            capabilities=[
                "text_generation",
                "code_generation",
                "summarization",
                "translation",
            ],
            dependencies=[
                "httpx",
                "pydantic",
                "backoff",
            ],  # Assuming these are the dependencies
            config_schema={
                "LLM_BACKEND": {"type": "string", "enum": [e.name for e in LLMBackend]},
                "LLM_MODEL_NAME": {"type": "string"},
                "LLM_API_KEY": {"type": "string", "sensitive": True},
                "LLM_TEMPERATURE": {"type": "number", "minimum": 0, "maximum": 2},
                "LLM_MAX_TOKENS": {"type": "integer"},
                "LLM_TIMEOUT": {"type": "integer"},
                "LLM_SYSTEM_PROMPT": {"type": "string"},
            },
        )

    def _load_model_config(self):
        """Loads and validates model configuration from the main config."""
        try:
            backend_str = self.config.get("LLM_BACKEND", "HUGGINGFACE_API").upper()
            backend = LLMBackend[backend_str]
            self.model_config = ModelConfig(
                model_name=self.config.get("LLM_MODEL_NAME", "gpt2"),
                backend=backend,
                api_key=self.config.get("LLM_API_KEY"),
                temperature=self.config.get("LLM_TEMPERATURE", 0.7),
                max_tokens=self.config.get("LLM_MAX_TOKENS", 512),
                timeout=self.config.get("LLM_TIMEOUT", 30),
                system_prompt=self.config.get(
                    "LLM_SYSTEM_PROMPT", "You are a helpful AI assistant."
                ),
            )
            self.logger.info(
                f"GeneralLLMPlugin loaded config for backend: {backend.name}, model: {self.model_config.model_name}"
            )
        except Exception as e:
            self.logger.error(f"Failed to load LLM model configuration: {e}")
            self._set_status(ComponentStatus.ERROR)

    def initialize(self) -> None:
        """Initializes the HTTP client for API-based backends."""
        super().initialize()
        if self.model_config and self.model_config.backend in [
            LLMBackend.HUGGINGFACE_API,
            LLMBackend.OPENAI,
            LLMBackend.ANTHROPIC,
            LLMBackend.GEMINI,
            LLMBackend.MISTRAL,
        ]:
            self.http_client = httpx.AsyncClient(timeout=self.model_config.timeout)
            self.logger.info(
                f"Initialized HTTP client for {self.model_config.backend.name} backend."
            )
        else:
            self.logger.info(
                f"No HTTP client needed for {self.model_config.backend.name} backend."
            )

    def shutdown(self) -> None:
        """Shuts down the HTTP client."""
        super().shutdown()
        if self.http_client:
            # In an async context, you'd use await self.http_client.aclose()
            # For a synchronous shutdown, just set to None for now.
            # If this plugin is meant to be purely synchronous, httpx.Client would be used instead.
            # Assuming this is called in a synchronous context, we'll just log and nullify.
            self.logger.info("Closing HTTP client for GeneralLLMPlugin.")
            self.http_client = None

    @backoff.on_exception(backoff.expo, httpx.RequestError, max_tries=3)
    async def generate_text(self, prompt: str, **kwargs) -> GenerationResult:
        """
        Generates text using the configured LLM backend.
        This is a placeholder and needs specific implementation for each backend.
        """
        if not self.model_config:
            self.logger.error("LLM model configuration not loaded.")
            return GenerationResult(
                text="Error: LLM not configured.",
                tokens_used=0,
                finish_reason="error",
                processing_time=0.0,
            )

        start_time = time.time()
        generated_text = ""
        tokens_used = 0
        finish_reason = "unknown"

        # Merge instance-level generation parameters with call-specific kwargs
        params = {
            "temperature": self.model_config.temperature,
            "max_tokens": self.model_config.max_tokens,
            "system_prompt": self.model_config.system_prompt,
            **kwargs,
        }

        try:
            if self.model_config.backend == LLMBackend.HUGGINGFACE_API:
                if not self.http_client:
                    raise Exception("HTTP client not initialized for HuggingFace API.")
                # Example for HuggingFace API, needs actual implementation based on specific API endpoint
                headers = (
                    {"Authorization": f"Bearer {self.model_config.api_key}"}
                    if self.model_config.api_key
                    else {}
                )
                response = await self.http_client.post(
                    f"https://api-inference.huggingface.co/models/{self.model_config.model_name}",
                    headers=headers,
                    json={
                        "inputs": prompt,
                        "parameters": {
                            "max_new_tokens": params["max_tokens"],
                            "temperature": params["temperature"],
                        },
                    },
                    timeout=self.model_config.timeout,
                )
                response.raise_for_status()
                result = response.json()
                generated_text = (
                    result[0]["generated_text"]
                    if result and isinstance(result, list)
                    else ""
                )
                # Hugging Face API doesn't easily provide tokens_used or finish_reason in this direct inference client
                tokens_used = len(generated_text.split())  # Simple approximation
                finish_reason = (
                    "length"
                    if len(generated_text.split()) >= params["max_tokens"]
                    else "completed"
                )

            elif self.model_config.backend == LLMBackend.OPENAI:
                if not self.http_client:
                    raise Exception("HTTP client not initialized for OpenAI.")
                # This requires 'openai' library, and using httpx directly might be complex for full API.
                # This is a conceptual example for direct HTTP client usage.
                # Better to use the official OpenAI client library.
                headers = {
                    "Authorization": f"Bearer {self.model_config.api_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": self.model_config.model_name,
                    "messages": [
                        {"role": "system", "content": params["system_prompt"]},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": params["temperature"],
                    "max_tokens": params["max_tokens"],
                }
                response = await self.http_client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.model_config.timeout,
                )
                response.raise_for_status()
                result = response.json()
                generated_text = result["choices"][0]["message"]["content"]
                tokens_used = result["usage"]["total_tokens"]
                finish_reason = result["choices"][0]["finish_reason"]

            # Add more backend implementations (Anthropic, Gemini, Mistral, Local) here
            # For HUGGINGFACE_LOCAL and LLAMA_CPP, you'd integrate with local inference servers or libraries.
            else:
                self.logger.warning(
                    f"Backend '{self.model_config.backend.name}' not yet fully implemented for text generation."
                )
                generated_text = f"Backend '{self.model_config.backend.name}' is not yet implemented."
                finish_reason = "not_implemented"

        except httpx.RequestError as exc:
            self.logger.error(
                f"Network error during LLM generation for {self.model_config.backend.name}: {exc}"
            )
            generated_text = f"Network error: {exc}"
            finish_reason = "network_error"
        except httpx.HTTPStatusError as exc:
            self.logger.error(
                f"HTTP error during LLM generation for {self.model_config.backend.name} - {exc.response.status_code}: {exc.response.text}"
            )
            generated_text = (
                f"API error: {exc.response.status_code} - {exc.response.text}"
            )
            finish_reason = "api_error"
        except Exception as e:
            self.logger.error(
                f"An unexpected error occurred during LLM generation: {e}"
            )
            generated_text = f"An unexpected error occurred: {e}"
            finish_reason = "exception"

        end_time = time.time()
        processing_time = end_time - start_time

        return GenerationResult(
            text=generated_text,
            tokens_used=tokens_used,
            finish_reason=finish_reason,
            processing_time=processing_time,
        )

    # You can add a stream_text method if your backends support streaming responses
    async def stream_text(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        Streams text generation from the LLM backend.
        This is a placeholder and needs specific implementation for each backend.
        """
        # Example: just yield the full text from generate_text for now
        # Real streaming would involve processing chunks from the API response
        try:
            result = await self.generate_text(prompt, **kwargs)
            yield result.text
        except Exception as e:
            self.logger.error(f"Error during streaming text: {e}")
            yield f"Error during streaming: {e}"
