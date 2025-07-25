from textual.app import App
from textual.widgets import (
    Header,
    Footer,
    TabbedContent,
    TabPane,
    Static,
    Button,
    Input,
    RichLog,
)
from osmanli_ai.widgets.quick_actions import quick_actions
from osmanli_ai.widgets.status import realm_health
from osmanli_ai.widgets.art import TITLE, ICONS
from rich.theme import Theme
import psutil
import logging

THEME = Theme(
    {
        "success": "#D4AF37 bold",  # Gold
        "error": "#9A3334 italic",  # Deep red
        "info": "#1E5F8B",  # Lapis blue
        "warning": "#FFD700",  # Bright gold
        "magic": "#8A2BE2",  # Sultan's purple
    }
)


class OttomanCLI(App):
    """An interactive, widget-based CLI for Osmanli AI."""

    CSS = """
    Screen {
        background: #000000;
    }

    Header {
        background: #8A2BE2;
        color: #D4AF37;
    }

    Footer {
        background: #8A2BE2;
        color: #D4AF37;
    }

    TabbedContent {
        background: #1E5F8B;
    }

    TabPane {
        background: #1E5F8B;
        border: thick #D4AF37;
        padding: 1 2;
    }
    Button {
        width: 100%;
        background: #D4AF37;
        color: #000000;
        border: round #9A3334;
        margin: 1 0;
    }
    Button:hover {
        background: #FFD700;
        border: round #9A3334;
    }
    """

    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self, assistant):
        super().__init__()
        self.assistant = assistant

    def compose(self):
        """Create child widgets for the app."""
        yield Header(name=TITLE)
        with TabbedContent(initial="system"):
            with TabPane(f"{ICONS['joust']} Code Tools", id="code_tools"):
                yield Button(f"{ICONS['joust']} Joust", id="joust", variant="primary")
                yield Button(
                    f"{ICONS['debugger_dungeon']} Debugger Dungeon",
                    id="debugger_dungeon",
                    variant="primary",
                )
                yield Button(
                    f"{ICONS['alchemy']} Alchemy", id="alchemy", variant="primary"
                )
            with TabPane(f"{ICONS['quran_explorer']} Knowledge", id="knowledge"):
                yield Button(
                    f"{ICONS['quran_explorer']} Quran Explorer",
                    id="quran_explorer",
                    variant="primary",
                )
                yield Button(
                    f"{ICONS['web_search']} Web Search",
                    id="web_search",
                    variant="primary",
                )
            with TabPane(f"{ICONS['settings']} System", id="system"):
                self.realm_health_widget = realm_health(self.console)
                self.cpu_task_id = self.realm_health_widget.tasks[0].id
                self.mem_task_id = self.realm_health_widget.tasks[1].id
                self.thought_process = RichLog(wrap=True)
                yield Static(quick_actions(), classes="quick-actions-table")
                yield Static(self.realm_health_widget, classes="realm-health-progress")
                yield Input(placeholder="Enter your decree...")
                yield self.thought_process
        yield Footer()

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        self.set_interval(1, self.update_realm_health)
        # Set up logging
        textual_handler = TextualLogHandler(self.thought_process)
        logging.getLogger().addHandler(textual_handler)
        logging.getLogger().setLevel(logging.INFO)
        self.log_thought("Welcome to the Imperial Dashboard!")

    def update_realm_health(self) -> None:
        """Update the realm health widget."""
        cpu_percent = psutil.cpu_percent()
        mem_percent = psutil.virtual_memory().percent

        self.realm_health_widget.update(
            self.cpu_task_id,
            description=f"CPU: {cpu_percent:.1f}%",
            completed=cpu_percent,
        )
        self.realm_health_widget.update(
            self.mem_task_id,
            description=f"MEM: {mem_percent:.1f}%",
            completed=mem_percent,
        )

    def log_thought(self, message: str):
        """Log a message to the thought process widget."""
        self.thought_process.write(message)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        command_map = {
            "joust": "start jousting arena",
            "debugger_dungeon": "enter debugger dungeon",
            "alchemy": "start code alchemy",
            "quran_explorer": "open quran explorer",
            "web_search": "perform web search",
        }
        command = command_map.get(event.button.id)
        if command:
            self.log_thought(
                f"Button '{event.button.id}' pressed. Sending command: '{command}'"
            )
            response = await self.assistant.process_query(command)
            self.log_thought(response)
        else:
            self.log_thought(
                f"Button '{event.button.id}' pressed. No specific command mapped."
            )
            response = await self.assistant.process_query(
                f"Tell me about {event.button.id}"
            )
            self.log_thought(response)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission events."""
        self.log_thought(f"Decree received: {event.value}")
        response = await self.assistant.process_query(event.value)
        self.log_thought(response)

    def action_quit(self) -> None:
        """An action to quit the app."""
        self.exit()


class TextualLogHandler(logging.Handler):
    """A logging handler that writes to a Textual RichLog widget."""

    def __init__(self, rich_log):
        super().__init__()
        self.rich_log = rich_log

    def emit(self, record):
        """Emit a log record."""
        self.rich_log.write(self.format(record))
