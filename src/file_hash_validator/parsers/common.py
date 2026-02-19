from __future__ import annotations

from pathlib import Path

from ..models import FileEntry, HashAlgo


class ManifestError(Exception):
    """Базовая ошибка манифеста (парсинг/валидация)"""


class ManifestValidationError(ManifestError):
    """ошибка структуры/значений вв манифесте."""


_HEX_CHARS = set("0123456789abcdef")


def _is_hex(s: str) -> bool:
    return all(ch in _HEX_CHARS for ch in s)


def normalize_expected_checksum(algo: HashAlgo, value: str) -> str:
    """
    Нормализуем контрольную сумму:
    - приводим к lowercase
    - проверяем hex-формат
    - проверяем длину
    - для CRC32: допускаем 1..8 hex-символов и дополняем нулями слева до 8
    """

    if not isinstance(value, str):
        raise ManifestValidationError("Поля 'hash' должно быть строкой")

    s = value.strip().lower()

    if not s:
        raise ManifestValidationError("Поля 'hash' не должно быть пустым")

    if not _is_hex(s):
        raise ManifestValidationError(
            "Поле 'hash' должно быть в hex-формате (0-9, a-f).")

    if algo == HashAlgo.MD5:
        if len(s) != 32:
            raise ManifestValidationError("Для md5 ожидается 32 hex-символа")
        return s

    if algo == HashAlgo.SHA256:
        if len(s) != 64:
            raise ManifestValidationError("Для sha256 ожидается 64 hex-символа")
        return s

    if algo == HashAlgo.CRC32:
        if not (1 <= len(s) <= 8):
            raise ManifestValidationError("Для crc32 ожидается 1-8 hex-символа")
        return s.zfill(8)

    # на случай, если будет неизвестный алгоритм
    raise ManifestValidationError(f"Неподдерживаемый алгоритм: {algo!r}")


def parse_algo(value: object) -> HashAlgo:
    """Преобразуем 'hash_type' в HashAlgo"""

    if not isinstance(value, str):
        raise ManifestValidationError("Поле 'hash_type' должно быть строкой.")

    raw = value.strip().lower()
    try:
        return HashAlgo(raw)
    except ValueError as e:
        raise ManifestValidationError(
            "Поле 'hash_type' должно быть одним из: crc32, md5, sha256"
        ) from e


def parse_entry(obj: object, workdir: Path) -> FileEntry:
    """
    Валидация и преобразование одной записи:
    - obj должен быть словарём
    - path/hash_type/hash обязательны
    - path резолвится относительно workdir, если он относительный
    """
    if not isinstance(obj, dict):
        raise ManifestValidationError(
            "Каждый элемент в 'files' должен быть объектом (словарём).")

    if "path" not in obj:
        raise ManifestValidationError("Отсутствует обязательное поле 'path'")
    if "hash_type" not in obj:
        raise ManifestValidationError("Отсутствует обязательное поле 'hash_type'.")
    if "hash" not in obj:
        raise ManifestValidationError("Отсутствует обязательное поле 'hash'.")

    path_value = obj["path"]
    if not isinstance(path_value, str) or not path_value.strip():
        raise ManifestValidationError("Поле 'path' должно быть непустой строкой")

    algo = parse_algo(obj["hash_type"])
    expected = normalize_expected_checksum(algo, obj["hash"])

    p = Path(path_value.strip())

    if not p.is_absolute():
        p = (workdir / p)

    return FileEntry(path=p, algo=algo, expected=expected)
