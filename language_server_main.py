# osmanli_ai/core/language_server.py

import importlib
import pkgutil
from pathlib import Path
from .language_server.plugins.plugin import LanguageServerPlugin


class LanguageServer:
    """
    Integrates with Language Server Protocols (LSP) for deep code intelligence.

    - Manages connections to different language servers.
    - Provides a unified interface for code completion, diagnostics, and more.
    - Detects the language of a file and routes requests to the appropriate server.
    """

    def __init__(self):
        self.servers = {}
        self._load_plugins()

    def _load_plugins(self):
        """Dynamically loads all language server plugins."""
        plugins_path = Path(__file__).parent / "language_server" / "plugins"
        for _, name, _ in pkgutil.iter_modules([str(plugins_path)]):
            try:
                module = importlib.import_module(
                    f".language_server.plugins.{name}", package="osmanli_ai.core"
                )
                for attribute_name in dir(module):
                    attribute = getattr(module, attribute_name)
                    if (
                        isinstance(attribute, type)
                        and issubclass(attribute, LanguageServerPlugin)
                        and attribute is not LanguageServerPlugin
                    ):
                        # Instantiate the plugin and add it to the servers dict
                        # The key can be the language name (e.g., python)
                        language_name = name.lower()
                        self.servers[language_name] = attribute()
                        print(f"Loaded language server plugin: {language_name}")
            except Exception as e:
                print(f"Failed to load plugin {name}: {e}")

    def get_completions(self, file_path, position):
        """
        Gets code completions for a given file and position.
        """
        language = Path(file_path).suffix[1:]
        if language in self.servers:
            return self.servers[language].get_completions(file_path, position)
        return []

    def get_diagnostics(self, file_path):
        """
        Gets diagnostics (errors, warnings) for a file.
        """
        language = Path(file_path).suffix[1:]
        if language in self.servers:
            return self.servers[language].get_diagnostics(file_path)
        return []
