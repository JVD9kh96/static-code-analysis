#!/usr/bin/env python3
"""
Small CLI that sums integers provided as arguments with argparse.
"""
from __future__ import annotations

import argparse
from typing import List


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sum integers")
    parser.add_argument("ints", nargs="+", type=int, help="integers to sum")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)
    total = sum(args.ints)
    print(total)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
