import logging
import importlib
from pathlib import Path

logger = logging.getLogger(__name__)


class PluginManager:
    """
    Loads and manages plugins.
    """

    def __init__(self, plugin_dir: str = "osmanli_ai/plugins"):
        self.plugin_dir = Path(plugin_dir)
        self.plugins = {}

    def load_plugins(self):
        """
        Loads all plugins from the plugin directory.
        """
        for plugin_path in self.plugin_dir.glob("*.py"):
            if plugin_path.name == "__init__.py":
                continue

            try:
                module_name = f"osmanli_ai.plugins.{plugin_path.stem}"
                module = importlib.import_module(module_name)
                self.plugins[plugin_path.stem] = module
                logger.info(f"Loaded plugin: {plugin_path.stem}")
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_path.stem}: {e}")

    def get_plugin(self, name: str):
        """
        Returns the plugin with the given name.
        """
        return self.plugins.get(name)
