import asyncio

from textual import work
from textual.validation import Integer
from textual.widgets import Input, RichLog
from textual.worker import Worker

from wieferich_prime_search.local import LogStr, SearchResults


class BatchSizeInput(Input):
    def on_mount(self) -> None:
        self.border_title = "Batch Size Per Core"
        self.border_subtitle = "Primes"
        self.type = "integer"
        self.validate_on = {"submitted"}
        self.validators = [Integer()]
        app_config = self.app.app_config
        self.placeholder = str(app_config.batch_size)


class DurationInput(Input):
    def on_mount(self) -> None:
        self.border_title = "Total Search Duration"
        self.border_subtitle = "Seconds"
        self.type = "Integer"
        self.validate_on = {"submitted"}
        self.validators = [Integer()]
        app_config = self.app.app_config
        self.placeholder = str(app_config.duration)


class AppLog(RichLog):

    def on_mount(self):
        self.highlight = True
        self.log_config_state()
        self.write("Ready to start searching ...")

    def log_config_state(self) -> None:
        app_config = self.app.app_config
        self.write(app_config.config_state)

    def log_session_result(self, results: SearchResults) -> None:
        self.write(results.session_results)
        self.log_config_state()

    def log_worker_status(self, search_worker: Worker[SearchResults]) -> None:
        self.write(f"{LogStr.get_timestamp()}: {search_worker.state}")

    @work
    async def log_searching(self, search_worker: Worker[SearchResults]) -> None:
        self.clear()
        self.log_config_state()
        self.log_worker_status(search_worker)
        while not search_worker.is_finished:
            await asyncio.sleep(2)

        if search_worker.error:
            self.write(f"Search failed: {search_worker.error}")
            return

        results = search_worker.result
        if not results:
            self.write("Search did not return results")
            return

        self.clear()
        self.log_session_result(results)
        self.log_worker_status(search_worker)
        self.write("Ready to start searching again ...")
