#!/usr/bin/env python3
"""
Load JSON from a file with careful error handling and explicit typing.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def load_json(path: str) -> Dict[str, Any]:
    """
    Load and return JSON object from the given file path.

    Raises:
        FileNotFoundError: if the file does not exist.
        json.JSONDecodeError: if the file is not valid JSON.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")
    with p.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise TypeError("Expected JSON object at top level")
    return data


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: perfect_1_load_json.py <path-to-json>")
        raise SystemExit(2)
    print(load_json(sys.argv[1]))
