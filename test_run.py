#!/usr/bin/env python3
"""
Unit Tests for Osmanli AI Application

This module contains test cases for the main application functionality.
"""

import logging
import unittest
from pathlib import Path
from unittest.mock import patch

# Import the module to test
from main import ImperialCore
from osmanli_ai.core.exceptions import ConfigurationError


class TestImperialCore(unittest.TestCase):
    """Test cases for the ImperialCore application class."""

    def setUp(self):
        """Set up test fixtures."""
        logging.basicConfig(level=logging.DEBUG)
        self.test_config = str(Path(__file__).parent.parent / "test_config.json")
        mock_args = type(
            "Args",
            (object,),
            {
                "config": self.test_config,
                "log_level": "INFO",
                "self_repair": False,
                "living_mode": False,
                "auto_repair_neovim": False,
                "repair_mode": False,
                "user_id": "test_user",
            },
        )()
        self.app = ImperialCore(mock_args)

    def tearDown(self):
        """Clean up after tests."""
        del self.app

    def test_config_loading(self):
        """Test that configuration loads correctly."""
        with patch("osmanli_ai.core.configuration_manager.Config") as MockConfig:
            MockConfig.return_value
            # The config is loaded during initialize
            # For this test, we just need to ensure Config is called correctly
            # when initialize is called.
            # Since initialize is async, we need to mock it or run it in an event loop.
            # For simplicity, we'll just check if Config is called.
            # A more robust test would would involve an async test runner.
            pass  # Placeholder, actual test logic will be more complex with async

    def test_plugin_loading(self):
        """Test plugin manager initialization."""
        with patch(
            "osmanli_ai.utils.plugin_manager_util.PluginManager"
        ) as MockPluginManager:
            MockPluginManager.return_value
            # PluginManager is initialized during app.initialize
            pass  # Placeholder, actual test logic will be more complex with async

    def test_invalid_config_path(self):
        """Test handling of invalid config path."""
        import asyncio

        with patch("osmanli_ai.core.configuration_manager.Config") as MockConfig:
            MockConfig.side_effect = ConfigurationError("Mock config error")

            mock_args = type(
                "Args",
                (object,),
                {
                    "config": "nonexistent_config.json",
                    "log_level": "INFO",
                    "self_repair": False,
                    "living_mode": False,
                    "auto_repair_neovim": False,
                    "repair_mode": False,
                    "user_id": "test_user",
                    "command": "dashboard",
                },
            )()
            app_with_invalid_config = ImperialCore(mock_args)

            result = asyncio.run(app_with_invalid_config.initialize())
            self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
