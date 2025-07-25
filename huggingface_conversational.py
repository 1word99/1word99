# osmanli_ai/plugins/huggingface_conversational.py

import logging
import traceback
import os

from transformers import AutoModelForCausalLM, AutoTokenizer

from osmanli_ai.plugins.base import BasePlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class Plugin(BasePlugin):
    """
    A concrete implementation of BasePlugin using Hugging Face's
    InferenceClient with configurable models and parameters.
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.model_name = self.config.get("HF_CHAT_MODEL", "microsoft/DialoGPT-medium")
        self.generation_params = self.config.get(
            "HF_CONVERSATIONAL_PARAMS",
            {
                "max_new_tokens": 100,
                "temperature": 0.7,
                "do_sample": True,
                "top_p": 1.0,
                "repetition_penalty": 1.0,
                "stop": ["\nUser:", "\nAI:", "<|endoftext|>"],
            },
        )
        self.tokenizer = None
        self.model = None
        logger.info(
            f"HuggingFaceConversationalPlugin initialized with model: {self.model_name}"
        )

    def initialize(self):
        super().initialize()
        self._initialize_model_and_tokenizer()

    def shutdown(self):
        super().shutdown()
        self.tokenizer = None
        self.model = None
        logger.info("HuggingFaceConversationalPlugin shut down.")

    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="HuggingFaceConversationalPlugin",
            version="0.2.0",  # Updated version due to significant changes
            author="Osmanli AI",
            description="Provides conversational AI capabilities using Hugging Face models with direct Transformers integration.",
            plugin_type=PluginType.LLM,
            capabilities=["conversational_ai", "text_generation", "model_switching"],
            dependencies=["transformers"],
        )

    def _initialize_model_and_tokenizer(self):
        """Initializes or re-initializes the tokenizer and model."""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            # Check for GPU availability and load model accordingly
            device = "cuda" if os.getenv("CUDA_VISIBLE_DEVICES", "") else "cpu"
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name).to(
                device
            )
            self.logger.info(
                f"HuggingFace model {self.model_name} and tokenizer initialized on {device}."
            )
        except Exception as e:
            self.logger.error(
                f"Failed to initialize HuggingFace model {self.model_name}: {e}\n{traceback.format_exc()}"
            )
            self.tokenizer = None
            self.model = None

    def process(self, query: str, context: dict = None) -> str:
        """
        Generate a conversational response using the configured model.

        Args:
            query (str): The user input.
            context (dict): Optional, for models that support conversation context.
                                 A dictionary that may contain 'chat_history'.

        Returns:
            str: The generated conversational response.
        """
        if self.model is None or self.tokenizer is None:
            return "Error: Conversational AI service not available. Model or tokenizer not initialized. Check logs for details."

        chat_history = context.get("chat_history", []) if context else []

        messages = []
        for user_msg, bot_msg in chat_history:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": bot_msg})
        messages.append({"role": "user", "content": query})

        try:
            # Apply chat template
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
            model_inputs = self.tokenizer([text], return_tensors="pt").to(
                self.model.device
            )

            # Generate the output
            generated_ids = self.model.generate(
                **model_inputs,
                max_new_tokens=self.generation_params.get("max_new_tokens", 100),
                temperature=self.generation_params.get("temperature", 0.7),
                do_sample=self.generation_params.get("do_sample", True),
                top_p=self.generation_params.get("top_p", 1.0),
                repetition_penalty=self.generation_params.get(
                    "repetition_penalty", 1.0
                ),
                pad_token_id=self.tokenizer.eos_token_id,  # Important for generation
            )

            # Get and decode the output
            output_ids = generated_ids[0][len(model_inputs.input_ids[0]) :]
            output = self.tokenizer.decode(output_ids, skip_special_tokens=True).strip()

            return output if output else "No conversational response generated."
        except Exception as e:
            self.logger.error(
                f"Error in HuggingFaceConversationalPlugin.process: {e}\n{traceback.format_exc()}"
            )
            return f"An error occurred while generating a response: {e}"

    def switch_model(self, new_model_name: str) -> str:
        """
        Switches the Hugging Face conversational model on the fly.

        Args:
            new_model_name (str): The new Hugging Face model repo ID to switch to.

        Returns:
            str: Confirmation or error message.
        """
        self.logger.info(f"Attempting to switch chat model to: {new_model_name}")
        prev_model_name = self.model_name
        prev_tokenizer = self.tokenizer
        prev_model = self.model

        self.model_name = new_model_name
        try:
            self._initialize_model_and_tokenizer()  # Re-initialize client with the new model
            if self.model and self.tokenizer:
                self.logger.info(
                    f"Successfully switched chat model to: {self.model_name}"
                )
                return (
                    f"Conversational model successfully switched to {self.model_name}."
                )
            else:
                raise Exception("Failed to initialize new model after switch.")
        except Exception as e:
            self.logger.error(f"Failed to switch chat model to {new_model_name}: {e}")
            self.model_name = prev_model_name  # Revert to old model name
            self.tokenizer = prev_tokenizer  # Revert to old tokenizer
            self.model = prev_model  # Revert to old model
            return f"Error: Could not switch to model {new_model_name}. Reverted to previous model ({prev_model_name}). Reason: {e}"
