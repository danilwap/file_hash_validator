from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from file_hash_validator.hashing import HashingError, calculate
from file_hash_validator.models import HashAlgo


def _write(tmp_path: Path, name: str, data: bytes) -> Path:
    """Функция для создания файла в tmp папке."""
    p = tmp_path / name
    p.write_bytes(data)
    return p


def test_calculate_md5_ok(tmp_path: Path) -> None:
    """MD5 должен корректно считаться для известного содержимого."""
    f = _write(tmp_path, "hello.txt", b"hello")
    assert calculate(f, HashAlgo.MD5) == "5d41402abc4b2a76b9719d911017c592"


def test_calculate_sha256_ok(tmp_path: Path) -> None:
    """SHA256 должен корректно считаться для пустого файла."""
    f = _write(tmp_path, "empty.bin", b"")
    assert calculate(f, HashAlgo.SHA256) == (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )


def test_calculate_crc32_ok(tmp_path: Path) -> None:
    """CRC32 должен считаться инкрементально и форматироваться в 8 hex-символов."""
    f = _write(tmp_path, "data.bin", b"123456789")
    # Канонический CRC32 для b"123456789" == 0xcbf43926
    assert calculate(f, HashAlgo.CRC32) == "cbf43926"


def test_calculate_streaming_chunk_size(tmp_path: Path) -> None:
    """Результат не должен зависеть от размера chunk'а (потоковое чтение)."""
    data = (b"abc" * 200_000) + (b"xyz" * 200_000)
    f = _write(tmp_path, "big.bin", data)

    h1 = calculate(f, HashAlgo.SHA256, chunk_size=7)
    h2 = calculate(f, HashAlgo.SHA256, chunk_size=1024 * 64)

    assert h1 == h2


def test_calculate_unsupported_algo(tmp_path: Path) -> None:
    """Неподдерживаемый алгоритм должен давать ValueError."""
    f = _write(tmp_path, "x.bin", b"hello")
    with pytest.raises(ValueError):
        calculate(f, "sha1")


def test_calculate_file_not_found(tmp_path: Path) -> None:
    """Отсутствующий файл должен давать HashingError с русским текстом."""
    f = tmp_path / "missing.bin"
    with pytest.raises(HashingError) as e:
        calculate(f, HashAlgo.MD5)
    assert "Файл не найден" in str(e.value)


def test_calculate_directory_instead_of_file(tmp_path: Path) -> None:
    """Каталог вместо файла должен давать HashingError."""
    d = tmp_path / "somedir"
    d.mkdir()

    with pytest.raises(HashingError) as e:
        calculate(d, HashAlgo.SHA256)
    assert "каталог" in str(e.value).lower()


@pytest.mark.skipif(os.name == "nt",
                    reason="chmod-тест прав чтения нестабилен на Windows")
def test_calculate_permission_denied(tmp_path: Path) -> None:
    """Если нет прав на чтение, должен быть HashingError."""
    f = _write(tmp_path, "secret.bin", b"topsecret")
    f.chmod(0)

    try:
        with pytest.raises(HashingError) as e:
            calculate(f, HashAlgo.MD5)
        assert "Нет прав" in str(e.value)
    finally:
        # вернуть права, чтобы tmp директория смогла удалиться
        f.chmod(stat.S_IRUSR | stat.S_IWUSR)


@pytest.mark.parametrize("algo", [HashAlgo.MD5, HashAlgo.SHA256, HashAlgo.CRC32])
def test_calculate_accepts_path_as_str(tmp_path: Path, algo: HashAlgo) -> None:
    """Функция должна принимать путь как строку."""
    f = _write(tmp_path, "file.bin", b"data")
    result = calculate(str(f), algo)
    assert isinstance(result, str)
    assert result  # непустая строка
