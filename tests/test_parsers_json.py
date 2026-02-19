from __future__ import annotations

from pathlib import Path

import pytest

from file_hash_validator.models import HashAlgo
from file_hash_validator.parsers.common import ManifestError, ManifestValidationError
from file_hash_validator.parsers.json_parser import load_json_manifest


def _write(tmp_path: Path, name: str, text: str) -> Path:
    """Функция для создания файла в tmp файле"""
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_load_json_manifest_ok(tmp_path: Path) -> None:
    """Корректный JSON должен распарситься в список FileEntry."""
    manifest = _write(
        tmp_path,
        "manifest.json",
        """
        {
          "files": [
            {
              "path": "data/file1.txt",
              "hash_type": "md5",
              "hash": "5d41402abc4b2a76b9719d911017c592"
            }
          ]
        }
        """,
    )

    workdir = tmp_path
    entries = load_json_manifest(manifest, workdir=workdir)

    assert len(entries) == 1
    assert entries[0].path == workdir / "data" / "file1.txt"
    assert entries[0].expected == "5d41402abc4b2a76b9719d911017c592"


def test_load_json_manifest_invalid_json(tmp_path: Path) -> None:
    """Битый JSON должен давать ManifestError."""
    manifest = _write(tmp_path, "bad.json",
                      '{"files": [ { "path": "a.txt" } ')  # нет закрывающих скобок

    with pytest.raises(ManifestError):
        load_json_manifest(manifest, workdir=tmp_path)


def test_load_json_manifest_unknown_hash_type(tmp_path: Path) -> None:
    """Неизвестный hash_type должен давать ManifestValidationError."""
    manifest = _write(
        tmp_path,
        "manifest.json",
        """
        {
          "files": [
            {"path": "a.txt", "hash_type": "md55", "hash": 
            "5d41402abc4b2a76b9719d911017c592"}
          ]
        }
        """,
    )

    with pytest.raises(ManifestValidationError):
        load_json_manifest(manifest, workdir=tmp_path)

def test_load_json_manifest_bad_md5_length(tmp_path: Path) -> None:
    """MD5 должен быть ровно 32 hex-символа."""
    manifest = _write(
        tmp_path,
        "manifest.json",
        """
        {
          "files": [
            {"path": "a.txt", "hash_type": "md5", "hash": "abc"}
          ]
        }
        """,
    )

    with pytest.raises(ManifestValidationError):
        load_json_manifest(manifest, workdir=tmp_path)

def test_load_json_manifest_crc32_zero_fill(tmp_path: Path) -> None:
    """CRC32 допускает 1..8 hex-символов и дополняется нулями слева до 8."""
    manifest = _write(
        tmp_path,
        "manifest.json",
        """
        {
          "files": [
            {"path": "a.txt", "hash_type": "crc32", "hash": "abc"}
          ]
        }
        """,
    )

    entries = load_json_manifest(manifest, workdir=tmp_path)

    assert len(entries) == 1
    assert entries[0].algo == HashAlgo.CRC32
    assert entries[0].expected == "00000abc"