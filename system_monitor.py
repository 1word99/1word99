from textual.widgets import Static
from rich.table import Table


class SystemMonitorWidget(Static):
    """A widget to display system monitor information."""

    def on_mount(self) -> None:
        self.update_monitor()
        self.set_interval(1, self.update_monitor)

    def update_monitor(self) -> None:
        """Update the monitor display."""
        table = Table(title="System Monitor")
        table.add_column("Metric")
        table.add_column("Value")

        if hasattr(self.app.core, "monitor"):
            stats = self.app.core.monitor.check_system()
            table.add_row("CPU Usage", f"{stats['cpu']:.2f}%")
            table.add_row("Memory Usage", f"{stats['memory']:.2f}%")

        self.update(table)
