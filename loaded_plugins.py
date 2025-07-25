from textual.widgets import Static
from rich.table import Table


class LoadedPluginsWidget(Static):
    """A widget to display loaded plugins."""

    def on_mount(self) -> None:
        self.update_plugins()
        self.set_interval(10, self.update_plugins)

    def update_plugins(self) -> None:
        """Update the plugins display."""
        table = Table(title="Loaded Plugins")
        table.add_column("Plugin Name")

        if (
            hasattr(self.app.core, "components")
            and "plugins" in self.app.core.components
        ):
            plugin_manager = self.app.core.components["plugins"]
            for plugin_name in plugin_manager.plugins.keys():
                table.add_row(plugin_name)

        self.update(table)
