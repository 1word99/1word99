"""
osmanli_ai/utils/configuration_manager.py
Configuration management system
"""

import json
import os
from pathlib import Path
from typing import Any, Dict

from osmanli_ai.core.exceptions import ConfigurationError


class Config:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.data = self._load_config()
        self._validate_config()

    def _validate_config(self):
        """Validate the configuration and set default values for missing keys."""
        # System defaults
        self.data.setdefault("system", {})
        self.data["system"].setdefault("log_level", "INFO")
        self.data["system"].setdefault("default_interface", "gui")
        self.data["system"].setdefault("interfaces", {})
        self.data["system"]["interfaces"].setdefault("neovim", {})
        self.data["system"]["interfaces"]["neovim"].setdefault("host", "127.0.0.1")
        self.data["system"]["interfaces"]["neovim"].setdefault("port", 8001)
        self.data["system"]["interfaces"]["neovim"].setdefault(
            "socket_path", "/tmp/nvim.sock"
        )

        # CLI defaults
        self.data.setdefault("cli", {})
        self.data["cli"].setdefault("voice_input_enabled", False)
        self.data["cli"].setdefault("voice_output_enabled", False)

        # Paths defaults
        self.data.setdefault("paths", {})
        self.data["paths"].setdefault("plugins_dir", "osmanli_ai/plugins")
        self.data["paths"].setdefault("quran_data", "data/quran_data.json")
        self.data["paths"].setdefault("model_storage", "data/models")

        # Modules defaults
        self.data.setdefault("modules", {})
        self.data["modules"].setdefault("quran", {})
        self.data["modules"]["quran"].setdefault("enabled", False)
        self.data["modules"]["quran"].setdefault(
            "quran_data_path", "/home/desktop/Desktop/box/curtain/quran_data.json"
        )
        self.data["modules"]["quran"].setdefault(
            "audio_base_url", "http://www.everyayah.com/data/Alafasy_128kbps/"
        )

        # Memory defaults
        self.data.setdefault("memory", {})
        self.data["memory"].setdefault("max_history_length", 50)

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file and merge with environment variables."""
        try:
            with open(self.config_path, "r") as f:
                config_data = json.load(f)
        except FileNotFoundError:
            raise ConfigurationError(f"Config file not found: {self.config_path}")
        except json.JSONDecodeError:
            raise ConfigurationError(f"Invalid JSON in config file: {self.config_path}")

        # Merge with environment variables
        for key, value in os.environ.items():
            if key == "HF_API_TOKEN":
                config_data["HF_API_TOKEN"] = value
            elif key == "FINANCE_API_KEY":
                config_data["FINANCE_API_KEY"] = value
            elif key == "STT_API_KEY":
                config_data["STT_API_KEY"] = value
            elif (
                key == "WEB_SEARCH_API_KEY"
            ):  # Assuming this is the name for web search API key
                config_data["WEB_SEARCH_API_KEY"] = value
            else:
                # Convert OSMANLI_AI_ prefixed environment variables to nested config
                if key.startswith("OSMANLI_AI_"):
                    config_key_path = key[len("OSMANLI_AI_") :].lower().split("_")

                    current_level = config_data
                    for i, part in enumerate(config_key_path):
                        if i == len(config_key_path) - 1:
                            current_level[part] = value
                        else:
                            if part not in current_level or not isinstance(
                                current_level[part], dict
                            ):
                                current_level[part] = {}
                            current_level = current_level[part]
        return config_data

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.data.get(key, default)

    def __contains__(self, key: str) -> bool:
        return key in self.data

    def self_test(self) -> bool:
        """Performs a self-test of the Config component.
        Returns True if the component is healthy, False otherwise.
        """
        # For now, a simple check that config data is loaded
        return bool(self.data)
