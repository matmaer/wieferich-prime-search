import os
import time
from collections.abc import Iterator
from concurrent.futures import Future, ProcessPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta

import gmpy2

from wieferich_prime_search.local import LogStr, SearchResults

NEXT_PRIME = gmpy2.next_prime
POWMOD = gmpy2.powmod
ONE_MPZ = gmpy2.mpz(1)
TWO_MPZ = gmpy2.mpz(2)


@dataclass
class SearchChunkResult:
    checked_primes: int
    last_prime_checked: int
    wieferich_primes: list[int]


def is_wieferich_prime(prime_number: int) -> bool:
    prime_mpz = gmpy2.mpz(prime_number)
    prime_squared = prime_mpz * prime_mpz
    return POWMOD(TWO_MPZ, prime_mpz - ONE_MPZ, prime_squared) == 1


def advance_prime(start_prime: int, prime_steps: int) -> int:
    current_prime = gmpy2.mpz(start_prime)

    for _ in range(prime_steps):
        current_prime = NEXT_PRIME(current_prime)

    return int(current_prime)


def get_primes_iterator(
    start_prime: gmpy2.mpz, prime_steps: int
) -> Iterator[gmpy2.mpz]:
    current_prime: gmpy2.mpz = start_prime
    for _ in range(prime_steps):
        current_prime = NEXT_PRIME(current_prime)
        yield current_prime


def search_prime_chunk(start_prime: int, prime_checks: int) -> SearchChunkResult:
    current_prime = gmpy2.mpz(start_prime)
    wieferich_primes: list[int] = []

    for _ in range(1, prime_checks + 1):
        current_prime = NEXT_PRIME(current_prime)
        current_prime_int = int(current_prime)
        if is_wieferich_prime(current_prime_int):
            wieferich_primes.append(current_prime_int)

    return SearchChunkResult(
        checked_primes=prime_checks,
        last_prime_checked=int(current_prime),
        wieferich_primes=wieferich_primes,
    )


class SearchExecutor:

    def __init__(self):
        self.checked_primes: int = 0
        self.check_every = 10000
        self.wieferich_primes: list[int] = []
        self.results = SearchResults()
        self.current_prime = self.results.latest_prime
        self.worker_count = os.cpu_count() or 1
        self.executor = ProcessPoolExecutor(max_workers=self.worker_count)
        self._worker_starts: list[int] | None = None

    def update_results(self) -> SearchResults:
        self.results.end_time = datetime.now().strftime(LogStr.PRETTY_FTIME)
        self.results.wieferich_primes = sorted(self.wieferich_primes)
        self.results.new_latest_prime = str(int(self.current_prime))
        self.results.total_primes_checked = str(self.checked_primes)
        self.results.completed = True
        self.results.save_session_result()
        return self.results

    def _init_worker_starts(self) -> list[int]:
        starts: list[int] = []
        current_start = int(self.current_prime)
        for _ in range(self.worker_count):
            starts.append(current_start)
            current_start = advance_prime(current_start, self.check_every)
        return starts

    def submit_search_chunks(self) -> list[Future[SearchChunkResult]]:
        if self._worker_starts is None:
            self._worker_starts = self._init_worker_starts()
        return [
            self.executor.submit(search_prime_chunk, start_prime, self.check_every)
            for start_prime in self._worker_starts
        ]

    def apply_chunk_results(self, chunk_results: list[SearchChunkResult]) -> bool:
        self._worker_starts = [
            chunk_result.last_prime_checked for chunk_result in chunk_results
        ]
        self.current_prime = max(self._worker_starts)
        self.checked_primes += sum(
            chunk_result.checked_primes for chunk_result in chunk_results
        )
        wieferich_primes = [
            wieferich_prime
            for chunk_result in chunk_results
            for wieferich_prime in chunk_result.wieferich_primes
        ]
        if not wieferich_primes:
            return False
        self.wieferich_primes.extend(wieferich_primes)
        return True

    def run_search_loop(self) -> SearchResults:
        duration = timedelta(seconds=10)
        deadline = time.monotonic() + duration.total_seconds()
        try:
            while time.monotonic() < deadline:
                futures = self.submit_search_chunks()
                chunk_results = [future.result() for future in futures]
                if self.apply_chunk_results(chunk_results):
                    return self.update_results()
        finally:
            self.executor.shutdown()
        return self.update_results()
