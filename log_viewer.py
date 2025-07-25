from textual.widgets import RichLog
from textual.reactive import reactive
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class LogViewerWidget(RichLog):
    """A widget to display logs."""

    log_file_path = reactive(Path("logs/osmanli_ai.log"))  # Assuming a default log file

    def on_mount(self) -> None:
        self.set_interval(1, self.read_logs)

    def read_logs(self) -> None:
        """Reads new lines from the log file and adds them to the RichLog."""
        try:
            if not self.log_file_path.exists():
                self.write("[red]Log file not found.[/red]")
                return

            with open(self.log_file_path, "r") as f:
                # Read all lines and only add new ones
                current_lines = f.readlines()
                new_lines = current_lines[
                    len(self.lines) :
                ]  # Assuming self.lines stores previous lines
                for line in new_lines:
                    self.write(line.strip())
                self.lines = current_lines  # Update stored lines

        except Exception as e:
            logger.error(f"Error reading log file: {e}")
            self.write(f"[red]Error reading logs: {e}[/red]")
