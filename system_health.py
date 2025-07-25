from textual.widgets import Static
from rich.table import Table


class SystemHealthWidget(Static):
    """A widget to display the health of the system."""

    def on_mount(self) -> None:
        self.update_health()
        self.set_interval(5, self.update_health)

    def update_health(self) -> None:
        """Update the health display."""
        table = Table(title="System Health")
        table.add_column("Component")
        table.add_column("Status")
        table.add_column("Message")

        if hasattr(self.app.core, "brain"):
            all_statuses = self.app.core.brain.component_status.get_all_statuses()
            for component_name, status_info in all_statuses.items():
                table.add_row(component_name, status_info["status"], status_info["message"])

        self.update(table)
