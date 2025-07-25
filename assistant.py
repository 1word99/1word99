# osmanli_ai/plugins/code/code_assistant_plugin.py

import logging
import os
import traceback

from huggingface_hub import InferenceClient

from osmanli_ai.plugins.base import BasePlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class Plugin(BasePlugin):
    """
    Integrates with a code generation/model inference service (e.g., Hugging Face Inference API)
    to provide code suggestions, adhering to the Osmanli AI plugin interface.
    """

    DEFAULT_STOP_SEQUENCES = ["\n\n", "```", "# End", "<|endoftext|>"]

    def __init__(self, config):
        super().__init__(config)
        # Get model from config, with a default fallback
        self.model_name = self.config.get("CODE_ASSISTANT_MODELS", {}).get(
            "default", "Salesforce/codegen-350M-mono"
        )
        self.hf_token_env = (
            "HF_API_TOKEN"  # Environment variable for the Hugging Face API token.
        )
        self.client = None
        self._initialize_client()
        self.logger.info(
            f"CodeAssistantPlugin initialized with model: {self.model_name}"
        )

    def initialize(self):
        super().initialize()
        self._initialize_client()
        self.logger.info("CodeAssistantPlugin activated.")

    def shutdown(self):
        super().shutdown()
        self.client = None
        self.logger.info("CodeAssistantPlugin shut down.")

    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="CodeAssistantPlugin",
            version="0.1.0",
            author="Osmanli AI",
            description="Provides code generation and completion capabilities.",
            plugin_type=PluginType.TOOL,
            capabilities=["code_generation", "code_completion", "model_switching"],
            dependencies=[],
        )

    def get_plugin_type(self) -> PluginType:
        return PluginType.TOOL

    def _initialize_client(self):
        """Initializes the Hugging Face Inference Client, handling missing tokens."""
        hf_token = self.config.get(self.hf_token_env)
        if not hf_token:
            self.logger.warning(
                f"{self.hf_token_env} not set in config. Code Assistant may not work."
            )
            self.client = None
            return
        try:
            self.client = InferenceClient(model=self.model_name, token=hf_token)
            self.logger.info(
                f"HuggingFace InferenceClient for CodeAssistant initialized with model: {self.model_name}"
            )
        except Exception as e:
            self.logger.error(
                f"Failed to initialize InferenceClient for CodeAssistant model {self.model_name}: {e}"
            )
            self.client = None

    def process(self, prompt: str, context: dict = None) -> str:
        """
        Generates code suggestions based on the provided prompt and context.

        Args:
            prompt (str): The code context or query for which to generate suggestions.
            context (dict, optional): Additional parameters like max_new_tokens, temperature, stop_sequences.
                                      These are merged with defaults from config.

        Returns:
            str: The generated code suggestion.
        """
        if self.client is None:
            return "Error: Code Assistant service is not initialized. Check logs for details."

        # Merge context parameters with config defaults
        generation_params = self.config.get("CODE_SUGGESTION_PARAMS", {})
        max_new_tokens = context.get(
            "max_new_tokens", generation_params.get("max_new_tokens", 200)
        )
        temperature = context.get(
            "temperature", generation_params.get("temperature", 0.3)
        )
        stop_sequences = context.get(
            "stop_sequences", generation_params.get("stop", self.DEFAULT_STOP_SEQUENCES)
        )

        self.logger.info(f"Generating code suggestion for prompt: {prompt[:50]}...")
        try:
            response_generator = self.client.text_generation(
                prompt=prompt,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=True,  # Often good for code generation to allow diversity
                stop=stop_sequences,
            )
            generated_code = "".join(chunk for chunk in response_generator).strip()
            self.logger.info("Code suggestion generated successfully.")
            return generated_code
        except Exception as e:
            self.logger.error(
                f"Error getting code suggestion with model {self.model_name}: {e}\n{traceback.format_exc()}"
            )
            if "authorization" in str(e).lower():
                return "Hugging Face Authorization Error. Please check your HF_API_TOKEN environment variable."
            return f"An error occurred during code suggestion: {e}"

    def switch_model(self, new_model_name: str) -> str:
        """
        Switches the code generation model at runtime.

        Args:
            new_model_name (str): The new Hugging Face model repo id.

        Returns:
            str: Confirmation or error message.
        """
        self.logger.info(
            f"Attempting to switch Code Assistant model to: {new_model_name}"
        )
        prev_model = self.model_name

        try:
            # Test the new model with a simple query before committing
            test_client = InferenceClient(
                model=new_model_name, token=os.getenv(self.hf_token_env)
            )
            test_client.text_generation(
                "def hello_world():", max_new_tokens=5
            )  # Quick check

            self.model_name = new_model_name
            self.client = test_client
            self.logger.info(
                f"Successfully switched Code Assistant model to: {self.model_name}"
            )
            return f"Code Assistant model successfully switched to {self.model_name}."
        except Exception as e:
            self.logger.error(
                f"Failed to switch Code Assistant model to {new_model_name}: {e}"
            )
            # Re-initialize the old client to maintain a working state
            self.model_name = prev_model  # Revert to previous model name
            self._initialize_client()  # Re-initialize the client with the previous model
            return f"Error: Could not switch to model {new_model_name}. Reverted to {prev_model}. Reason: {e}"
