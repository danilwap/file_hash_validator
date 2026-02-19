from __future__ import annotations

from pathlib import Path

import pytest

from file_hash_validator.models import HashAlgo
from file_hash_validator.parsers.common import ManifestError, ManifestValidationError
from file_hash_validator.parsers.xml_parser import load_xml_manifest


def _write(tmp_path: Path, name: str, text: str) -> Path:
    """Функция для создания файла в tmp файле"""
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_load_xml_manifest_ok(tmp_path: Path) -> None:
    """Корректный XML должен распарситься в список FileEntry."""
    manifest = _write(tmp_path,
                      "manifest.json",
                      """<files>
                                <file>
                                    <path>data/file1.txt</path>
                                    <hash_type>md5</hash_type>
                                    <hash>5d41402abc4b2a76b9719d911017c592</hash>
                                </file>
                            
                                <file>
                                    <path>data/file2.txt</path>
                                    <hash_type>sha256</hash_type>
                                    <hash>e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855</hash>
                                </file>
                            
                                <file>
                                    <path>/absolute/path/file3.bin</path>
                                    <hash_type>crc32</hash_type>
                                    <hash>1a2b3c4d</hash>
                                </file>
                            </files>
                      """)

    workdir = tmp_path
    entries = load_xml_manifest(manifest, workdir=workdir)

    assert len(entries) == 3
    assert entries[0].path == workdir / "data" / "file1.txt"
    assert entries[0].algo == "md5"
    assert entries[0].expected == "5d41402abc4b2a76b9719d911017c592"

@pytest.mark.parametrize("broken_xml", [
    "<files><file></files>",                 # незакрытый тег
    "<files><file/></files><extra/>",        # мусор после корня
])
def test_load_xml_manifest_invalid_xml(tmp_path: Path, broken_xml) -> None:
    """Битый XML должен давать ManifestError."""
    manifest = _write(tmp_path, "broken.xml", broken_xml)  # нет закрывающих скобок

    with pytest.raises(ManifestError):
        load_xml_manifest(manifest, workdir=tmp_path)


def test_load_xml_manifest_unknown_hash_type(tmp_path: Path) -> None:
    """Неизвестный hash_type должен давать ManifestValidationError."""
    manifest = _write(tmp_path,
                      "manifest.json",
                      """<files>
                                <file>
                                    <path>data/file1.txt</path>
                                    <hash_type>md52</hash_type>
                                    <hash>5d41402abc4b2a76b9719d911017c592</hash>
                                </file>
                            </files>
                      """)

    with pytest.raises(ManifestValidationError):
        load_xml_manifest(manifest, workdir=tmp_path)


def test_load_xml_manifest_bad_md5_length(tmp_path: Path) -> None:
    """MD5 должен быть ровно 32 hex-символа."""
    manifest = _write(tmp_path,
                      "manifest.json",
                      """<files>
                                <file>
                                    <path>data/file1.txt</path>
                                    <hash_type>crc32</hash_type>
                                    <hash>5d41402abc4b2a76b9719d911017c5922</hash>
                                </file>
                            </files>
                      """)

    with pytest.raises(ManifestValidationError):
        load_xml_manifest(manifest, workdir=tmp_path)


def test_load_json_manifest_crc32_zero_fill(tmp_path: Path) -> None:
    """CRC32 допускает 1..8 hex-символов и дополняется нулями слева до 8."""
    manifest = _write(tmp_path,
                      "manifest.json",
                      """<files>
                                <file>
                                    <path>data/file1.txt</path>
                                    <hash_type>crc32</hash_type>
                                    <hash>abc</hash>
                                </file>
                            </files>
                      """)

    entries = load_xml_manifest(manifest, workdir=tmp_path)

    assert len(entries) == 1
    assert entries[0].algo == HashAlgo.CRC32
    assert entries[0].expected == "00000abc"
