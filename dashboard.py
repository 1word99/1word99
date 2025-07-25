from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text


class ImperialDashboard:
    def __init__(self):
        self.tabs = {
            "️ Code Tools": ["Joust", "Debugger Dungeon", "Alchemy"],
            "️ Code Agent": [],
            "️ Finance": ["Quran Explorer", "Web Search"],
            "⚙️ System": ["Self-Repair", "Neovim Bridge", "Settings"],
        }

    def render(self):
        layout = Layout()
        layout.split_column(
            Layout(Panel("Osmanli AI - Imperial Dashboard", style="gold_on_dark_red")),
            Layout(self._render_tabs()),
        )
        return layout

    def _render_tabs(self):
        tabs_ui = ""
        for tab, widgets in self.tabs.items():
            tabs_ui += f"\n[bold]{tab}[/]\n" + "\n".join(
                f"  [link]{w}[/link]" for w in widgets
            )
        return Panel(Text(tabs_ui, justify="left"))
