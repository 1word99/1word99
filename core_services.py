from textual.widgets import Static
from rich.table import Table


class CoreServicesWidget(Static):
    """A widget to display the status of core services."""

    def on_mount(self) -> None:
        self.update_services()
        self.set_interval(5, self.update_services)

    def update_services(self) -> None:
        """Update the services display."""
        table = Table(title="Core Services")
        table.add_column("Service")
        table.add_column("Status")

        if hasattr(self.app.core, "brain"):
            table.add_row(
                "AICortex", "Active" if self.app.core.brain.active else "Inactive"
            )
            table.add_row(
                "Repair Worker",
                "Running"
                if self.app.core.brain.repair_thread.is_alive()
                else "Stopped",
            )
            table.add_row(
                "Analysis Worker",
                "Running"
                if self.app.core.brain.analysis_thread.is_alive()
                else "Stopped",
            )
            table.add_row(
                "Optimization Worker",
                "Running"
                if self.app.core.brain.optimization_thread.is_alive()
                else "Stopped",
            )
            table.add_row(
                "Decision Worker",
                "Running"
                if self.app.core.brain.decision_thread.is_alive()
                else "Stopped",
            )
            table.add_row(
                "Security Worker",
                "Running"
                if self.app.core.brain.security_thread.is_alive()
                else "Stopped",
            )

        self.update(table)
