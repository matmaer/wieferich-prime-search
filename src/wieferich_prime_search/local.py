from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path


class BtnLabel(StrEnum):
    start = "Start Search"
    stop = "Stop & Save"


class LogStr(StrEnum):
    PRETTY_FTIME = "%Y-%m-%d %H:%M:%S"
    NA = "not available"

    @staticmethod
    def get_timestamp():
        return datetime.now().strftime(LogStr.PRETTY_FTIME)


@dataclass
class AppConfig:
    duration: int = 10
    batch_size: int = 1000000
    keep_one_core_free: bool = False

    @property
    def config_state(self) -> str:
        return "\n".join(
            [
                "Current App Config",
                "------------------",
                f"Total Search Duration: {self.duration}",
                f"Batch Size Per Core: {self.batch_size}",
                f"Keep One Core Free: {self.keep_one_core_free}",
                "\n",
            ]
        )


@dataclass(frozen=True, slots=True)
class LocalPaths:
    module_dir: Path = Path(__file__).parent
    data_dir: Path = module_dir / "data"
    latest_prime_file: Path = data_dir / "latest_prime.txt"

    @property
    def new_session_result_file(self) -> Path:
        return self.data_dir / "last_session_results.txt"


@dataclass(slots=True)
class SearchResults:
    latest_prime: int = 2**64
    start_time: str = LogStr.NA
    end_time: str = LogStr.NA
    new_latest_prime: str = LogStr.NA
    total_primes_checked: str = LogStr.NA
    wieferich_primes: list[int] = field(default_factory=lambda: [])
    completed: bool = False
    _local_paths: LocalPaths = LocalPaths()

    def __post_init__(self) -> None:
        self.start_time = datetime.now().strftime(LogStr.PRETTY_FTIME)
        self.latest_prime = int(
            self._local_paths.latest_prime_file.read_text(encoding="utf-8")
        )

    @property
    def session_results(self) -> str:
        return "\n".join(
            [
                "Wieferich Prime Search Session Report",
                "=====================================",
                f"Start time: {self.start_time}",
                f"End time: {self.end_time}",
                f"First prime checked: {self.latest_prime}",
                f"Last prime checked: {self.new_latest_prime}",
                f"Total primes checked: {self.total_primes_checked}",
                f"Wieferich primes found: {self.wieferich_primes or None}",
                f"Completed batch: {self.completed}",
                "\n",
            ]
        )

    def save_session_result(self) -> None:
        self._local_paths.new_session_result_file.write_text(
            self.session_results + "\n", encoding="utf-8"
        )
        self._local_paths.latest_prime_file.write_text(self.new_latest_prime)
