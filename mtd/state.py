import os
from .paths import STATE_FILE

ALL_LIST_NAME = "ALL"
RESERVED_LIST_NAMES = [ALL_LIST_NAME]
CURRENT_LIST_KEY = 'CURRENT_LIST'
ADDITIONAL_LISTS_KEY = 'ADDITIONAL_LISTS'

def get_current_list() -> str:
    """Get the current list from the state file. Returns 'ALL' if file doesn't exist or is invalid."""
    if not os.path.exists(STATE_FILE):
        return ALL_LIST_NAME

    list_name = _read_state_value(CURRENT_LIST_KEY)
    if list_name is None:
        return ALL_LIST_NAME
    
    return list_name


def set_current_list(list_name: str) -> None:
    """Set the current list in the state file."""
    additional_lists = get_additional_lists()
    _write_state(list_name, additional_lists)


def get_additional_lists() -> list[str]:
    """Get the list of additional lists from the state file."""
    lists_str = _read_state_value(ADDITIONAL_LISTS_KEY)
    if not lists_str:
        return []
    
    return [l.strip() for l in lists_str.split(',') if l.strip()]


def add_additional_list(list_name: str) -> None:
    """Add a list to the additional lists in the state file."""
    additional_lists = get_additional_lists()
    
    assert list_name not in additional_lists
    
    additional_lists.append(list_name)
    additional_lists.sort()
    
    current_list = get_current_list() or ALL_LIST_NAME
    _write_state(current_list, additional_lists)


def remove_additional_list(list_name: str) -> None:
    """Remove a list from the additional lists in the state file."""
    additional_lists = get_additional_lists()
    if list_name in additional_lists:
        additional_lists.remove(list_name)
    
    current_list = get_current_list() or ALL_LIST_NAME
    _write_state(current_list, additional_lists)


def _read_state_value(key: str) -> str | None:
    """Read a value from the state file for the given key."""
    if not os.path.exists(STATE_FILE):
        return None
    
    try:
        with open(STATE_FILE, 'r') as file:
            for line in file:
                line = line.strip()
                if line and '=' in line:
                    line_key, value = line.split('=', 1)
                    if line_key.strip() == key:
                        return value.strip()
    except (IOError, ValueError):
        pass
    
    return None


def _write_state(current_list: str, additional_lists: list[str]) -> None:
    """Write the current list and additional lists to the state file."""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as file:
        file.write(f'{CURRENT_LIST_KEY}={current_list}\n')
        if additional_lists:
            file.write(f'{ADDITIONAL_LISTS_KEY}={",".join(sorted(additional_lists))}\n')
