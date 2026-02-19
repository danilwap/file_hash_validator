# Точка входа при запуске через:
# python -m file_hash_validator
from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
