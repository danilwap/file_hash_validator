from __future__ import annotations

import json
from pathlib import Path

from ..models import FileEntry
from .common import ManifestError, ManifestValidationError, parse_entry


def load_json_manifest(manifest_path: Path, workdir: Path) -> list[FileEntry]:
    """
    Загружает JSON Файл-спсико и возращает список FileEntry
    """

    try:
        text = manifest_path.read_text(encoding="utf-8")
    except OSError as e:
        raise ManifestError(
            f"Не удалось прочитать файл: {manifest_path}") from e

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ManifestError(f"Некорректный JSON: {e}") from e

    if not isinstance(data, dict):
        raise ManifestValidationError("Корень JSON должен быть объектом (словарём).")

    files = data.get("files")

    if files is None:
        raise ManifestValidationError("Отсутствует обязательное поле 'files'.")
    if not isinstance(files, list):
        raise ManifestValidationError("Поле 'files' должно быть массивом.")

    result: list[FileEntry] = []

    for i, item in enumerate(files, start=1):
        try:
            result.append(parse_entry(item, workdir=workdir))
        except ManifestValidationError as e:
            raise ManifestValidationError(f"Ошибка в files[{i}]: {e}") from e
    return result
