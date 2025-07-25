from textual.widgets import Static
from rich.table import Table


class SecurityStatusWidget(Static):
    """A widget to display security status."""

    def on_mount(self) -> None:
        self.update_security_status()
        self.set_interval(10, self.update_security_status)

    def update_security_status(self) -> None:
        """Update the security status display."""
        table = Table(title="Security Status")
        table.add_column("Metric")
        table.add_column("Value")

        if hasattr(self.app.core, "brain") and hasattr(
            self.app.core.brain, "security_scanner"
        ):
            # This is a placeholder. In a real scenario, the security_scanner
            # would store its findings, and we would display them here.
            table.add_row("Last Scan", "N/A")
            table.add_row("Vulnerabilities Found", "0")

        self.update(table)
