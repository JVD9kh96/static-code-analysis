"""
Language registry – maps file extensions and language names to profiles.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.languages.base import LanguageProfile


def get_profile(lang_name: str) -> LanguageProfile:
    """Return a language profile by name (e.g. ``"python"``, ``"csharp"``)."""
    name = lang_name.strip().lower()
    if name in ("python", "py"):
        from src.languages.python_lang import PythonProfile
        return PythonProfile()
    if name in ("csharp", "cs", "c#"):
        from src.languages.csharp_lang import CSharpProfile
        return CSharpProfile()
    raise ValueError(f"Unsupported language: {lang_name!r}")


def detect_profile(file_path: str) -> Optional[LanguageProfile]:
    """Auto-detect a language profile from the file extension."""
    ext = Path(file_path).suffix.lower()
    mapping = {
        ".py": "python",
        ".cs": "csharp",
    }
    lang = mapping.get(ext)
    if lang is None:
        return None
    return get_profile(lang)


SUPPORTED_EXTENSIONS = {".py", ".cs"}
