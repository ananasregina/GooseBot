from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, RichLog, DataTable, ProgressBar, TabbedContent, TabPane
from textual.binding import Binding
from textual.reactive import reactive
from textual.css.query import NoMatches
import asyncio
from .events import RequestUpdateEvent, LogEvent, BotStatusEvent, RequestStatus

class RequestRow(Static):
    """A widget to represent a single request's progress"""
    
    status = reactive(RequestStatus.RECEIVED)
    progress = reactive(0.0)
    
    def __init__(self, event: RequestUpdateEvent):
        super().__init__(id=f"req-{event.request_id}")
        self.request_id = event.request_id
        self.user = event.user
        self.channel = event.channel
        self.content = event.message_content
        self.status = event.status
    
    def compose(self) -> ComposeResult:
        with Horizontal(classes="request-header"):
            yield Static(f"[bold]{self.user}[/] in [dim]{self.channel}[/]: {self.content[:30]}...", classes="request-info")
            yield Static(self.status.value.upper(), id=f"status-{self.request_id}", classes="request-status")
        yield ProgressBar(total=100, show_eta=False, id=f"progress-{self.request_id}")

    def watch_status(self, status: RequestStatus):
        try:
            status_widget = self.query_one(f"#status-{self.request_id}", Static)
            status_widget.update(status.value.upper())
        except:
            pass

    def watch_progress(self, progress: float):
        try:
            pb = self.query_one(f"#progress-{self.request_id}", ProgressBar)
            pb.progress = progress * 100
        except:
            pass

class GooseTUI(App):
    """GooseBot Terminal User Interface"""
    
    CSS = """
    RequestRow {
        border: solid green;
        margin: 1 1;
        padding: 0 1;
        height: 4;
    }
    .request-header {
        height: 1;
    }
    .request-info {
        width: 1fr;
    }
    .request-status {
        width: 15;
        text-align: right;
    }
    #log-view {
        border: solid blue;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("d", "switch_tab('dashboard')", "Dashboard"),
        Binding("l", "switch_tab('logs')", "Logs"),
        Binding("s", "switch_tab('settings')", "Settings"),
    ]
    
    bot_connected = reactive(False)
    guild_count = reactive(0)
    bot_name = reactive("Unknown")
    
    def __init__(self, event_queue: asyncio.Queue):
        super().__init__()
        self.event_queue = event_queue
        self.active_requests = {}

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(initial="dashboard"):
            with TabPane("Dashboard", id="dashboard"):
                yield Static(id="bot-status-bar", content="Bot status: Disconnected")
                yield Vertical(id="requests-container")
            with TabPane("Logs", id="logs"):
                yield RichLog(id="log-view", highlight=True, markup=True)
            with TabPane("Settings", id="settings"):
                yield Static("Settings will be available here in the future.")
        yield Footer()

    async def on_mount(self):
        self.set_interval(0.1, self.process_events)
        # Force a status refresh
        self._update_status_bar()

    async def process_events(self):
        count = 0
        while count < 50:
            count += 1
            try:
                event = self.event_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            except Exception:
                continue

            if isinstance(event, LogEvent):
                try:
                    log_view = self.query_one("#log-view", RichLog)
                    color = "white"
                    if event.level == "ERROR": color = "red"
                    elif event.level == "WARNING": color = "yellow"
                    elif event.level == "DEBUG": color = "grey"
                    log_view.write(f"[{color}]{event.timestamp:.2f} - {event.level} - {event.message}[/]")
                except NoMatches:
                    pass
            
            elif isinstance(event, BotStatusEvent):
                self.bot_connected = event.is_connected
                self.guild_count = event.guild_count
                self.bot_name = event.user_name

            elif isinstance(event, RequestUpdateEvent):
                try:
                    container = self.query_one("#requests-container")
                    if event.request_id not in self.active_requests:
                        row = RequestRow(event)
                        self.active_requests[event.request_id] = row
                        await container.mount(row)
                    else:
                        row = self.active_requests[event.request_id]
                        row.status = event.status
                        row.progress = event.progress
                except NoMatches:
                    pass

    def watch_bot_connected(self, connected: bool):
        self._update_status_bar()

    def watch_guild_count(self, count: int):
        self._update_status_bar()

    def watch_bot_name(self, name: str):
        self._update_status_bar()

    def _update_status_bar(self):
        try:
            status_bar = self.query_one("#bot-status-bar", Static)
            if self.bot_name == "Unknown" and not self.bot_connected:
                status_bar.update("Bot Status: [bold red]Initializing...[/]")
            else:
                status_bar.update(f"Bot: [bold]{self.bot_name}[/] | Guilds: {self.guild_count} | Status: {'[green]Connected[/]' if self.bot_connected else '[red]Disconnected[/]'}")
        except NoMatches:
            pass

    def action_switch_tab(self, tab: str):
        try:
            self.query_one(TabbedContent).active = tab
        except Exception:
            pass
