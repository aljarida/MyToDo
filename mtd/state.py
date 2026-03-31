import os
from .paths import STATE_FILE

ALL_LIST_NAME = "ALL"
RESERVED_LIST_NAMES = [ALL_LIST_NAME]
CURRENT_LIST_KEY = "CURRENT_LIST"
ADDITIONAL_LISTS_KEY = "ADDITIONAL_LISTS"

def get_current_list() -> str:
    """Get the current list from the state file. Returns 'ALL' if file doesn't exist or is invalid."""
    if not os.path.exists(STATE_FILE):
        return ALL_LIST_NAME

    list_name = _read_state_value(CURRENT_LIST_KEY)
    if list_name is None:
        return ALL_LIST_NAME
    else: 
        return list_name


def get_lists() -> list[str]:
    """Get the list of additional lists from the state file."""
    lists_str = _read_state_value(ADDITIONAL_LISTS_KEY)
    if not lists_str:
        lists = []
    else:
        lists = [l.strip() for l in lists_str.split(',') if l.strip()]
    
    return lists

def select_list(list_name: str) -> None:
    """Set the current list in the state file."""
    _write_state(selected_list=list_name)


def add_list_or_lists(*list_names: str) -> None:
    """Add one or more lists to the state list."""
    all_lists = get_lists()

    for name in list_names:
        if name in all_lists:
            print(f"Failed to add any new list. '{name}' already exists in the database.")
            return
    
    all_lists.extend(list_names)

    _write_state(all_lists=all_lists)


def remove_list(list_name: str) -> None:
    """Remove a list from the additional lists in the state file."""
    if list_name == ALL_LIST_NAME:
        print(f"Failed to remove list '{ALL_LIST_NAME}'. '{ALL_LIST_NAME}' is reserved and cannot be removed.")
        return

    all_lists = get_lists()
    if list_name not in all_lists:
        print(f"Failed to remove list '{list_name}'. The provided list could not be found.")
        return

    all_lists.remove(list_name)
    _write_state(all_lists=all_lists)


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


def _write_state(*, selected_list: str | None = None, all_lists: list[str] | None = None) -> None:
    """Write the current list and additional lists to the state file."""
    if all_lists is None:
        all_lists = get_lists()

    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as file:
        if selected_list is not None:
            file.write(f'{CURRENT_LIST_KEY}={selected_list}\n')

        if ALL_LIST_NAME not in all_lists:
            all_lists.append(ALL_LIST_NAME)

        all_lists.sort()
        csv = ",".join(all_lists)
        file.write(f'{ADDITIONAL_LISTS_KEY}={csv}\n')
