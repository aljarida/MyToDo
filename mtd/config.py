import os

from .paths import (
    DATA_DIR,
    DATA_FILES,
    PLAINTEXT_DIR,
    ENCRYPTED_DIR,
)


def prepare_directory_and_files() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PLAINTEXT_DIR, exist_ok=True)
    os.makedirs(ENCRYPTED_DIR, exist_ok=True)

    for file in DATA_FILES:
        if not os.path.exists(file):
            with open(file, 'w') as _:
                pass
