from textual.widgets import Static
from rich.table import Table


class KnowledgeBaseWidget(Static):
    """A widget to display knowledge base statistics."""

    def on_mount(self) -> None:
        self.update_kb()
        self.set_interval(5, self.update_kb)

    def update_kb(self) -> None:
        """Update the knowledge base display."""
        table = Table(title="Knowledge Base")
        table.add_column("Category")
        table.add_column("Count")

        if hasattr(self.app.core, "brain") and hasattr(
            self.app.core.brain, "knowledge_base"
        ):
            kb = self.app.core.brain.knowledge_base
            table.add_row(
                "Total Repairs", str(sum(len(v) for v in kb.data["repairs"].values()))
            )
            table.add_row(
                "Total Optimizations",
                str(sum(len(v) for v in kb.data["optimizations"].values())),
            )

        self.update(table)
