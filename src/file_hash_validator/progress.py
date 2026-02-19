from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, TextIO


def _fmt_bytes(n: int) -> str:
    # Человеческий формат: B, KiB, MiB, GiB
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    x = float(n)
    i = 0
    while x >= 1024.0 and i < len(units) - 1:
        x /= 1024.0
        i += 1
    if i == 0:
        return f"{int(x)} {units[i]}"
    return f"{x:.1f} {units[i]}"


@dataclass
class Progress:
    """
    Простой консольный прогресс:
      - всегда: "проверено N из M"
      - опционально: прогресс байт по текущему файлу (если размер известен)
    """
    total_files: int
    stream: TextIO = sys.stderr
    enabled: bool = True
    min_interval_sec: float = 0.08  # анти-спам в консоль

    checked_files: int = 0
    current_file: Optional[Path] = None
    current_size: Optional[int] = None
    current_read: int = 0

    _last_draw_ts: float = 0.0

    @classmethod
    def from_entries(cls, total_files: int, *, stream: TextIO = sys.stderr,
                     enabled: bool = True) -> "Progress":
        return cls(total_files=total_files, stream=stream, enabled=enabled)

    def start(self) -> None:
        if not self.enabled:
            return
        self._draw(force=True)

    def file_started(self, path: Path, size: Optional[int]) -> None:
        self.current_file = path
        self.current_size = size if (size is None or size >= 0) else None
        self.current_read = 0
        if not self.enabled:
            return
        self._draw(force=True)

    def bytes_advanced(self, n: int) -> None:
        if n > 0:
            self.current_read += n
        if not self.enabled:
            return
        self._draw()

    def file_finished(self) -> None:
        self.checked_files += 1
        self.current_file = None
        self.current_size = None
        self.current_read = 0
        if not self.enabled:
            return
        self._draw(force=True)

    def finish(self) -> None:
        if not self.enabled:
            return
        # финальный вывод отдельной строкой
        self._draw(force=True, endline=True)

    def _draw(self, *, force: bool = False, endline: bool = False) -> None:
        now = time.monotonic()
        if not force and (now - self._last_draw_ts) < self.min_interval_sec:
            return
        self._last_draw_ts = now

        base = f"проверено {self.checked_files} из {self.total_files}"
        detail = ""

        # байтовый прогресс только если идёт файл и размер известен
        if self.current_file is not None and self.current_size is not None:
            size = self.current_size
            read = min(self.current_read, size) if size > 0 else self.current_read
            if size > 0:
                pct = int((read / size) * 100)
                detail = f" | {pct:3d}% ({_fmt_bytes(read)} / {_fmt_bytes(size)})"
            else:
                # размер 0 — показываем 100% сразу
                detail = " | 100% (0 B / 0 B)"

        text = base + detail

        # Каретка: обновляем одну строку
        if endline:
            self.stream.write("\r" + text + "\n")
        else:
            self.stream.write("\r" + text)
        self.stream.flush()
