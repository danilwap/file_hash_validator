from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .hashing import HashingError, calculate
from .models import FileEntry
from .progress import Progress


@dataclass(frozen=True, slots=True)
class CheckResult:
    total: int
    ok: int
    mismatched: list[tuple[FileEntry, str]]
    read_errors: list[tuple[FileEntry, HashingError]]


def _safe_size(path: Path) -> int | None:
    try:
        return path.stat().st_size
    except OSError:
        return None


def check_entries(entries: Iterable[FileEntry], *, progress_enabled: bool = True) -> CheckResult:
    entries_list = list(entries)
    prog = Progress.from_entries(len(entries_list), enabled=progress_enabled)
    prog.start()

    ok = 0
    mismatched: list[tuple[FileEntry, str]] = []
    read_errors: list[tuple[FileEntry, HashingError]] = []

    for entry in entries_list:
        size = _safe_size(entry.path)
        prog.file_started(entry.path, size)

        try:
            actual = calculate(entry.path, entry.algo, on_read=prog.bytes_advanced)

            if actual.lower() == entry.expected.lower():
                ok += 1
            else:
                mismatched.append((entry, actual))

        except HashingError as e:
            read_errors.append((entry, e))

        finally:
            prog.file_finished()

    prog.finish()
    return CheckResult(
        total=len(entries_list),
        ok=ok,
        mismatched=mismatched,
        read_errors=read_errors,
    )
