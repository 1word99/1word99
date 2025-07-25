# osmanli_ai/utils/plugin_manager.py
import importlib
import inspect
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

from osmanli_ai.base import BaseComponent, ComponentStatus
from osmanli_ai.plugins.base import BasePlugin

logger = logging.getLogger(__name__)


class PluginManager:
    """Hybrid plugin manager with backward compatibility"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.plugins: Dict[str, Union[BaseComponent, Any]] = {}
        self.plugins_dir = Path(config.get("plugins_dir", "osmanli_ai/plugins"))
        self.excluded_plugin_paths = [
            Path("osmanli_ai/core/language_server/plugins").resolve()
        ]

    async def load_plugins(self) -> None:
        """Load plugins with automatic fallback"""
        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory missing: {self.plugins_dir}")
            return

        logger.debug(f"Scanning for plugins in: {self.plugins_dir}")
        for plugin_file in self.plugins_dir.glob("**/*.py"):
            logger.debug(f"Found file: {plugin_file.name}")
            if (
                plugin_file.name.startswith(("_", "."))
                or plugin_file.name == "__init__.py"
                or plugin_file.name == "base.py"  # Skip base.py
                or any(
                    str(plugin_file.resolve()).startswith(str(p))
                    for p in self.excluded_plugin_paths
                )
            ):
                logger.debug(
                    f"Skipping hidden, special, __init__.py, base.py, or excluded file: {plugin_file.name} (Path: {plugin_file.resolve()})"
                )
                continue

            try:
                logger.debug(f"Attempting to load plugin from: {plugin_file.name}")
                plugin = self._load_single_plugin(plugin_file)
                if plugin:
                    logger.debug(
                        f"Successfully loaded plugin class from {plugin_file.name}"
                    )
                    self._initialize_and_register(plugin, plugin_file.name)
                else:
                    logger.warning(f"No valid plugin class found in {plugin_file.name}")
            except Exception as e:
                logger.error(
                    f"Plugin loading failed for {plugin_file.name}: {e}", exc_info=True
                )

    def _load_single_plugin(self, plugin_file: Path) -> Optional[Any]:
        """Flexible plugin loading supporting multiple patterns"""
        module_name = f"osmanli_ai.plugins.{plugin_file.stem}"
        import sys

        sys.path.insert(0, str(plugin_file.parent))
        spec = importlib.util.spec_from_file_location(module_name, plugin_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.path.pop(0)

        # Check for plugin classes in order of preference
        for name, cls in inspect.getmembers(module, inspect.isclass):
            if issubclass(cls, BasePlugin) and cls is not BasePlugin:
                return cls(self.config)
        return None

    def _initialize_and_register(self, plugin: Any, plugin_file_name: str) -> None:
        """Handle initialization for all plugin types"""
        try:
            # Initialize based on detected type
            if hasattr(plugin, "initialize"):
                plugin.initialize()

                # Set status if supported
                if hasattr(plugin, "status"):
                    if isinstance(plugin, BaseComponent):
                        plugin.status = ComponentStatus.RUNNING

                # Register with appropriate name
                name = plugin.get_metadata().name
                self.plugins[name] = plugin
                logger.info(
                    f"Loaded plugin: {name} with status: {plugin.status.name if hasattr(plugin, 'status') else 'N/A'}"
                )
            else:
                logger.error(
                    f"Plugin {plugin_file_name} does not have a 'metadata.name' attribute. Skipping registration."
                )
        except Exception as e:
            self._handle_initialization_error(plugin, e, plugin_file_name)

    def _handle_initialization_error(
        self, plugin: Any, error: Exception, plugin_file_name: str = "Unknown"
    ) -> None:
        """Consistent error handling for all plugin types"""
        if hasattr(plugin, "status"):
            if isinstance(plugin, BaseComponent):
                plugin.status = ComponentStatus.ERROR

        name = getattr(plugin, "name", plugin.__class__.__name__)
        logger.error(f"Initialization failed for {name}: {error}")

    def get_plugin(self, name: str) -> Optional[Any]:
        """Get plugin by name with type hints"""
        return self.plugins.get(name)

    def get_all_plugins(self) -> Dict[str, Any]:
        """Get all loaded plugins"""
        return self.plugins

    async def shutdown(self) -> None:
        pass

    def self_test(self) -> bool:
        """Performs a self-test of the PluginManager component.
        Returns True if the component is healthy, False otherwise.
        """
        logger.info("Running self-test for PluginManager...")
        import asyncio
        import shutil
        import tempfile

        test_plugins_dir = None
        try:
            # Create a temporary directory for test plugins
            test_plugins_dir = Path(tempfile.mkdtemp())
            # Create a dummy plugin file
            dummy_plugin_content = """
from osmanli_ai.plugins.base import BasePlugin, PluginMetadata, PluginType

class Plugin(BasePlugin):
    def __init__(self, config):
        super().__init__(config)
    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="DummyPlugin",
            version="1.0.0",
            author="Test",
            description="A dummy plugin for testing.",
            plugin_type=PluginType.TOOL,
            capabilities=["test_capability"],
            dependencies=[],
        )
    def get_plugin_type(self) -> PluginType:
        return PluginType.TOOL
    def initialize(self):
        pass
    def shutdown(self):
        pass
    def process(self, query: str, context: dict = None) -> str:
        return "Dummy response"
"""
            (test_plugins_dir / "dummy_plugin.py").write_text(dummy_plugin_content)

            # Temporarily change plugins_dir to the test directory
            original_plugins_dir = self.plugins_dir
            self.plugins_dir = test_plugins_dir

            # Test loading the dummy plugin
            self.plugins.clear()  # Clear existing plugins for a clean test
            asyncio.run(self.load_plugins())

            if "DummyPlugin" not in self.plugins:
                logger.error("PluginManager self-test failed: Dummy plugin not loaded.")
                return False

            logger.info("PluginManager self-test passed.")
            return True
        except Exception as e:
            logger.error(f"PluginManager self-test failed: {e}")
            return False
        finally:
            # Restore original plugins_dir and clean up temporary directory
            if test_plugins_dir and test_plugins_dir.exists():
                shutil.rmtree(test_plugins_dir)
            self.plugins_dir = original_plugins_dir
