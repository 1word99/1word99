from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn


def realm_health(console: Console) -> Progress:
    progress = Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=20, complete_style="red", finished_style="gold"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    )
    progress.add_task("CPU", total=100)
    progress.add_task("MEM", total=100)
    return progress
