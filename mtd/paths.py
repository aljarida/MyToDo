import os
import sys

# File paths
SCRIPT_DIR: str = os.path.dirname(os.path.realpath(sys.argv[0]))
DATA_DIR: str = os.path.join(SCRIPT_DIR, '.mtd')
PLAINTEXT_DIR: str = os.path.join(DATA_DIR, 'plaintext')
ENCRYPTED_DIR: str = os.path.join(DATA_DIR, 'encrypted')
INCOMPLETE_TASKS_FILE: str = os.path.join(PLAINTEXT_DIR, 'tasks.json')
COMPLETED_TASKS_FILE: str = os.path.join(PLAINTEXT_DIR, 'completed_tasks.json')
LOG_FILE: str = os.path.join(PLAINTEXT_DIR, 'history.log')

DATA_FILES: list = [INCOMPLETE_TASKS_FILE, COMPLETED_TASKS_FILE, LOG_FILE]
TASK_FILES: list = [INCOMPLETE_TASKS_FILE, COMPLETED_TASKS_FILE]


def get_encrypted_file_path(file_path: str) -> str:
    """Get the path for an encrypted file within the encrypted directory."""
    filename = os.path.basename(file_path)
    return os.path.join(ENCRYPTED_DIR, filename)

