#!/usr/bin/env python3
"""
A small frozen dataclass with explicit types and an example method.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    id: int
    username: str
    email: str

    def display_name(self) -> str:
        """Return a safe display name."""
        return f"{self.username} <{self.email}>"


def create_example() -> User:
    return User(id=1, username="alice", email="alice@example.com")


if __name__ == "__main__":
    u = create_example()
    print(u.display_name())
