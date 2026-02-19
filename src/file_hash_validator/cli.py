from __future__ import annotations

import argparse
from pathlib import Path


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
        help="Путь к файлу-списку (JSON или XML)."
    )

    return parser
def main():
    """
    Основная функция запуска программы.
    Возращает код завершения.
    """
    parser = build_parser()
    args = parser.parse_args()

    manifest: Path = args.manifest

    #Определяем формат по расширению файла
    fmt = manifest.suffix.lower().lstrip(".")

    print(f"Файл-список: {manifest}")
    print(f"Определённый формат: {fmt or "Неизвестный"}")