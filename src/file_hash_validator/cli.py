from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .checker import check_entries
from .parsers.common import ManifestError, ManifestValidationError
from .parsers.json_parser import load_json_manifest
from .parsers.xml_parser import load_xml_manifest



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
        help="Рабочая директория для относительных путей "
             "(по умолчанию: текущая директория).",
    )

    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Не показывать прогресс выполнения.",
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

    try:
        if fmt == "json":
            entries = load_json_manifest(manifest_path, workdir=workdir)
        elif fmt == "xml":
            entries = load_xml_manifest(manifest_path, workdir=workdir)
        else:
            print("Неизвестный формат файла. Используйте .json или .xml")
            return 2
    except (ManifestError, ManifestValidationError) as e:
        print(f"Ошибука манифеста: {e}")
        return 2
    except OSError as e:
        print(f"Ошибка чтения файла: {e}")
        return 2

    print(f"Успешно загружено записей: {len(entries)}")

    if not entries:
        return 0

    # прогресс по умолчанию включаем только если stderr — терминал
    progress_enabled = (not args.no_progress) and sys.stderr.isatty()

    result = check_entries(entries, progress_enabled=progress_enabled)

    print(f"Готово. Успешно: {result.ok}/{result.total}")

    if result.read_errors:
        print("\nОшибки чтения файлов:")
        for entry, err in result.read_errors:
            print(f"- {entry.path} [{entry.algo.value}]: {err}")

    if result.mismatched:
        print("\nНесовпадения контрольных сумм:")
        for entry, actual in result.mismatched:
            print(f"- {entry.path} [{entry.algo.value}]: ожидается {entry.expected}, получено {actual}")

        # коды завершения:
        # 0 — всё ок
        # 1 — есть несовпадения/ошибки чтения
    return 0 if (not result.mismatched and not result.read_errors) else 1