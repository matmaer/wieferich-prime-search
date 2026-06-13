import os
import shutil
import traceback
from pathlib import Path

from wieferich_prime_search.gui.app import WieferichPrimeSearch

STACK_TRACE_PATH = Path(__file__).parent / "stacktrace.log"
if STACK_TRACE_PATH.exists():
    STACK_TRACE_PATH.unlink()


def run_app():
    if shutil.which("git") is None:
        print("git not found, progress cannot be updated")
        return

    if os.environ.get("WIEFERICH_DEV_MODE") == "1":

        def save_stacktrace():
            with Path.open(STACK_TRACE_PATH, "a") as f:
                traceback.print_exc(file=f)

        class WieferichPrimeSearchDev(WieferichPrimeSearch):
            CSS_PATH = Path("gui", "gui.tcss")

            def _handle_exception(self, error: Exception) -> None:
                save_stacktrace()
                super()._handle_exception(error)

        try:
            app = WieferichPrimeSearchDev()
            app.run()

        except Exception:
            save_stacktrace()
            raise

    else:
        app = WieferichPrimeSearch()
        app.run()


if __name__ == "__main__":
    run_app()
