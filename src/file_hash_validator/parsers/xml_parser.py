from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from ..models import FileEntry
from .common import ManifestError, ManifestValidationError, parse_entry


def _get_required_text(parent: ET.Element, tag: str) -> str:
    """
    Достаём текст из обязательного дочернего тега.
    """
    child = parent.find(tag)
    if child is None:
        raise ManifestValidationError(f"Отсутствует обязательный тег <{tag}>.")
    text = (child.text or "").strip()
    if not text:
        raise ManifestValidationError(f"Тег <{tag}> не должен быть пустым.")
    return text


def load_xml_manifest(manifest_path: Path, workdir: Path) -> list[FileEntry]:
    """
    Загружает XML файл-список и возвращает список FileEntry.
    """
    try:
        text = manifest_path.read_text(encoding="utf-8")
    except OSError as e:
        raise ManifestError(
            f"Не удалось прочитать файл: {manifest_path}") from e

    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        raise ManifestError(f"Некорректный XML: {e}") from e

    if root.tag != "files":
        raise ManifestValidationError("Корневой тег XML должен быть <files>.")

    result: list[FileEntry] = []

    # Каждый файл — это <file>...</file>
    files = list(root.findall("file"))
    if not files:
        raise ManifestValidationError(
            "Внутри <files> должен быть хотя бы один тег <file>.")

    for i, file_el in enumerate(files, start=1):
        try:
            path = _get_required_text(file_el, "path")
            hash_type = _get_required_text(file_el, "hash_type")
            checksum = _get_required_text(file_el, "hash")

            # Приводим XML-запись к виду, который понимает общий валидатор
            obj = {"path": path, "hash_type": hash_type, "hash": checksum}

            result.append(parse_entry(obj, workdir=workdir))
        except ManifestValidationError as e:
            raise ManifestValidationError(f"Ошибка в file[{i}]: {e}") from e

    return result
