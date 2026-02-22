#!/usr/bin/env python3
"""
Stream lines from a file that match a compiled regular expression.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Iterator, Pattern


def match_lines(path: str, pattern: str) -> Iterator[str]:
    """
    Yield lines from file at `path` that match `pattern`.
    """
    compiled: Pattern[str] = re.compile(pattern)
    p = Path(path)
    with p.open("r", encoding="utf-8") as fh:
        for line in fh:
            if compiled.search(line):
                yield line.rstrip("\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: perfect_3_stream_matches.py <file> <regex>")
        raise SystemExit(2)
    for matched in match_lines(sys.argv[1], sys.argv[2]):
        print(matched)
