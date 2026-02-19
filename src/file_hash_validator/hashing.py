from __future__ import annotations

import hashlib
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union, Callable

from .models import HashAlgo

DEFAULT_CHUNK_SIZE = 1024 * 1024

@dataclass
class HashingError(Exception):
    """Ошибка расчёта контрольной суммы (чтение/доступ к файлу)."""
    message: str
    path: Path
    cause: Optional[BaseException] = None

    def __str__(self) -> str:
        base = f"{self.message}: {self.path}"
        return f"{base} ({self.cause})" if self.cause else base


def _normalize_algo(algo: Union[HashAlgo, str]) -> HashAlgo:
    if isinstance(algo, HashAlgo):
        return algo
    if not isinstance(algo, str):
        raise ValueError(f"Неподдерживаемый тип алгоритма: {type(algo)!r}")
    s = algo.strip().lower()
    try:
        return HashAlgo(s)
    except ValueError as e:
        raise ValueError(f"Неподдерживаемый алгоритм: {algo!r}") from e


def calculate(
    path: Union[Path, str],
    algo: Union[HashAlgo, str],
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    on_read: Callable[[int], None] | None = None,
) -> str:
    """
    calculate(path, algo) -> str
    - потоковое чтение chunk'ами
    - CRC32 инкрементально, результат hex lowercase (8 символов)
    - MD5 / SHA256 через hashlib
    - ошибки чтения файла оборачиваются в HashingError
    """
    p = path if isinstance(path, Path) else Path(path)
    a = _normalize_algo(algo)

    # Предварительные проверки
    try:
        if not p.exists():
            raise HashingError("Файл не найден", p)
        if p.is_dir():
            raise HashingError("Указан каталог вместо файла", p)
    except OSError as e:
        raise HashingError("Ошибка доступа к пути", p, e) from e

    try:
        with p.open("rb") as f:
            if a is HashAlgo.CRC32:
                crc = 0
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    if on_read:
                        on_read(len(chunk))
                    crc = zlib.crc32(chunk, crc)
                return f"{crc & 0xFFFFFFFF:08x}"

            h = hashlib.new(a.value)
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                if on_read:
                    on_read(len(chunk))
                h.update(chunk)
            return h.hexdigest()

    except FileNotFoundError as e:
        raise HashingError("Файл не найден", p, e) from e
    except PermissionError as e:
        raise HashingError("Нет прав на чтение файла", p, e) from e
    except IsADirectoryError as e:
        raise HashingError("Указан каталог вместо файла", p, e) from e
    except OSError as e:
        raise HashingError("Ошибка ввода-вывода при чтении файла", p, e) from e