from __future__ import annotations

import argparse
from pathlib import Path

from .parsers.common import ManifestError, ManifestValidationError
from .parsers.json_parser import load_json_manifest


def build_parser() -> argparse.ArgumentParser:
    """
        Парсер аргументов командной строки
    """
    parser = argparse.ArgumentParser(
        prog="file-hash-validator",
        description="Утилита для проверки контрольных сумм файлов из JSON/"
                    "XML файла-списка."
    )

    # Обязательный аргумент - путь к файлу списку
    parser.add_argument(
        "manifest",
        type=Path,
        help="Путь к файлу-списку (JSON или XML).",
    )

    parser.add_argument(
        "--workdir",
        type=Path,
        default=Path.cwd(),
        help="Рабочая директория для относительных путей (по умолчанию: текущая директория).",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """
    Основная функция запуска программы.
    Возращает код завершения.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    manifest_path: Path = args.manifest
    workdir: Path = args.workdir

    # Определяем формат по расширению файла
    fmt = manifest_path.suffix.lower().lstrip(".")

    if fmt != "json":
        print("Пока реализован только JSON-парсер")
        return 2

    try:
        entries = load_json_manifest(manifest_path, workdir=workdir)
    except (ManifestError, ManifestValidationError) as e:
        print(f"Ошибука манифеста: {e}")
        return 2
    except OSError as e:
        print(f"Ошибка чтения файла: {e}")
        return 2

    print(f"Успешно загружено записей: {len(entries)}")

    if entries:
        print(f"Первая запись: path={entries[0].path} algo={entries[0].algo.value} "
              f"hash={entries[0].expected}")
