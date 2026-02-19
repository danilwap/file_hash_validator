# File Hash Validator

Консольная утилита для проверки контрольных сумм файлов на основании манифеста в формате **JSON** или **XML**.

Поддерживаемые алгоритмы:
- CRC32
- MD5
- SHA256

Утилита рассчитывает контрольные суммы указанных файлов и проверяет их совпадение со значениями из файла-списка.

---
## Установка

Требуется Python 3.10+
### 1 Клонирование репозитория

```bash
git clone https://github.com/danilwap/file_hash_validator.git
cd file-hash-validator
```

### 2 Создание и активация виртуального окружения

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

### 3 Установка пакета

```bash
pip install .
```

### 4 Запуск проекта

```bash
file-hash-validator <path-to-manifest> [--workdir <directory>] [--no-progress]

file-hash-validator sample.xml
```

## Параметры

| Параметр | Описание |
|----------|----------|
| `path-to-manifest` | Путь к JSON или XML файлу со списком файлов |
| `--workdir` | Рабочая директория для относительных путей (по умолчанию — директория запуска утилиты) |
| `--no-progress` | Не показывать прогресс выполнения |

## Формат манифеста

Манифест должен содержать список объектов со следующими полями:

- `path` — путь к файлу  
- `hash_type` — тип контрольной суммы (`crc32`, `md5`, `sha256`)  
- `hash` — ожидаемое значение контрольной суммы  

---

### Пример JSON

```json
[
  {
    "path": "example.txt",
    "hash_type": "md5",
    "hash": "5d41402abc4b2a76b9719d911017c592"
  },
  {
    "path": "data.bin",
    "hash_type": "sha256",
    "hash": "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
  }
]
```

### Пример XML

```xml
<files>
  <file>
    <path>example.txt</path>
    <hash_type>md5</hash_type>
    <hash>5d41402abc4b2a76b9719d911017c592</hash>
  </file>
  <file>
    <path>data.bin</path>
    <hash_type>sha256</hash_type>
    <hash>2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824</hash>
  </file>
</files>
```
