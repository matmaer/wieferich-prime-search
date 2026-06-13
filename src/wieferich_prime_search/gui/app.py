import asyncio
from typing import ClassVar

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, HorizontalGroup
from textual.widgets import Button, Footer, Header, Input, ProgressBar
from textual.worker import Worker

from wieferich_prime_search.executor import SearchExecutor
from wieferich_prime_search.local import AppConfig, BtnLabel, SearchResults

from .widgets import AppLog, BatchSizeInput, DurationInput


class WieferichPrimeSearch(App[None]):

    BINDINGS: ClassVar = [
        Binding(
            "ctrl+s",
            action="stop_and_save",
            description="Stop and Save",
            key_display="ctrl-s",
            priority=True,
        )
    ]

    CSS_PATH = "gui.tcss"

    def __init__(self) -> None:
        self.app_config = AppConfig()
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Header(icon="\u2261")  # IDENTICAL TO
        yield Horizontal(DurationInput(), BatchSizeInput(), classes="actionables")
        yield HorizontalGroup(
            Button(BtnLabel.start, id="start_button"),
            ProgressBar(total=float(self.app_config.duration), disabled=True),
        )
        yield AppLog(highlight=True)
        yield Footer()

    def on_mount(self) -> None:
        self.progress_bar = self.query_exactly_one(ProgressBar)
        self.app_log = self.query_exactly_one(AppLog)
        self.start_button = self.query_one("#start_button", Button)
        self._search_worker: Worker[SearchResults] | None = None

    @on(Input.Submitted)
    def update_duration(self, event: Input.Submitted) -> None:
        if isinstance(event.input, DurationInput):
            self.notify("new duration" + event.value)
        elif isinstance(event.input, BatchSizeInput):
            self.notify("new batch size" + event.value)

    @on(Button.Pressed)
    def handle_button_press(self, event: Button.Pressed) -> None:
        if event.button.label == BtnLabel.start:
            event.stop()
            if self._search_worker and not self._search_worker.is_finished:
                self.notify("Search already in progress")
                return
            self.start_button.disabled = True
            self._search_worker = self.start_search()
            self.app_log.log_searching(self._search_worker)
            self.update_progress_bar(self._search_worker)

    @work
    async def start_search(self) -> SearchResults:
        search_executor = SearchExecutor()
        return await asyncio.to_thread(search_executor.run_search_loop)

    @work
    async def update_progress_bar(self, search_worker: Worker[SearchResults]) -> None:
        self.progress_bar.update(total=float(self.app_config.duration), progress=0)
        elapsed = 0
        while not search_worker.is_finished:
            await asyncio.sleep(1)
            elapsed += 1
            self.progress_bar.update(progress=min(elapsed, self.app_config.duration))
        self.progress_bar.update(progress=float(self.app_config.duration))

    def action_stop_and_save(self) -> None:
        self.notify("to be implemented")
