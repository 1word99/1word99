from rich import box
from rich.table import Table


def quick_actions() -> Table:
    table = Table(box=box.ROUNDED)
    table.add_column("Action")
    table.add_column("Hotkey")
    table.add_row(" Decree", "/d")
    table.add_row("️ Toggle Guard", "/g")
    table.add_row(" Open Bazaar", "/b")
    return table
