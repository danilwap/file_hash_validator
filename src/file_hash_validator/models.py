from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class HashAlgo(str, Enum):
    """Поддерживаемы алгоритмы контрольных сумм."""
    CRC32 = "crc32"
    MD5 = "md5"
    SHA256 = "sha256"


@dataclass(frozen=True, slots=True)
class FileEntry:
    """Одна запись из файл-списка"""
    path: Path
    algo: HashAlgo
    expected: str
