#!/usr/bin/env python3
"""
A simple thread-safe counter using threading.Lock.
"""
from __future__ import annotations

from threading import Lock, Thread
from typing import Callable


class Counter:
    def __init__(self) -> None:
        self._value = 0
        self._lock = Lock()

    def increment(self) -> None:
        with self._lock:
            self._value += 1

    def value(self) -> int:
        with self._lock:
            return self._value


def worker(counter: Counter, n: int) -> None:
    for _ in range(n):
        counter.increment()


if __name__ == "__main__":
    c = Counter()
    threads = [Thread(target=worker, args=(c, 10000)) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("Final value:", c.value())
