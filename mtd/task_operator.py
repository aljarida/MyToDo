import json
import os
from datetime import datetime
from typing import Optional
from collections import defaultdict

from .paths import TASK_FILES, get_encrypted_file_path
from .enums import PrintFormat
from .task import Task
from .state import (
    get_current_list, set_current_list, RESERVED_LIST_NAMES, ALL_LIST_NAME,
    get_additional_lists, add_additional_list, remove_additional_list
)


class TaskOperator:
    """
    Provides primary operations on tasks: Creating, deleting, reading, printing, et c.

    TaskOperator is instantiated once to complete tasks. It either reads data or reads AND writes data, then terminates.
    Each instance of TaskOperator performs a single action, and thus it does not juggle state as a user calls MTD repeatedly.
    """
    def __init__(self, incomplete_tasks_path: str, completed_tasks_path: str, log_file_path: str) -> None:
        """
        Initialize a TaskOperator. Requires paths to incomplete and complete tasks as well as log as the log file.
        """
        self.incomplete_tasks_path: str = incomplete_tasks_path
        self.completed_tasks_path: str = completed_tasks_path
        self.log_file_path: str = log_file_path
        self.tasks: list[Task] = []
        self.current_time: datetime = datetime.now()
        self.current_list: str = get_current_list()


    def add_task(self, text, priority=None) -> None:
        """Write task to incomplete tasks file via appending, then print the updated task-list."""
        self._read_tasks(self.incomplete_tasks_path)
        new_task = Task(text, list_name=self.current_list)
        self.tasks.append(new_task)
        self._write_tasks_to_file(self.incomplete_tasks_path, self.tasks, 'w')
        self._print_and_log(f'Added task "{text}" to {self.current_list}.')


    def complete_tasks(self, indices) -> None:
        """Complete all tasks based on supplied task positions (relative to current list)."""
        filtered_tasks = self._get_sorted_filtered_tasks(self.incomplete_tasks_path)
        indices = self._convert_negatives(indices, len(filtered_tasks))
        tasks_to_complete = [filtered_tasks[idx - 1] for idx in indices if 1 <= idx <= len(filtered_tasks)]
        
        if not tasks_to_complete:
            print(f'No tasks found with the specified indices.')
            return
        
        task_uuids_to_complete = {task.task_uuid for task in tasks_to_complete}
        tasks_to_complete = [task for task in self.tasks if task.task_uuid in task_uuids_to_complete]
        
        for task in tasks_to_complete:
            task.mark_end_time()

        self._write_completed_tasks_to_file(self.completed_tasks_path, tasks_to_complete)
        for task in tasks_to_complete:
            self._print_and_log(f'Completed "{task.text}".')

        remaining_tasks = [task for task in self.tasks if task.task_uuid not in task_uuids_to_complete]
        self._write_tasks_to_file(self.incomplete_tasks_path, remaining_tasks, 'w')


    def delete_incomplete_tasks_by_indices(self, indices, completing_tasks=False) -> None:
        """Delete tasks based on supplied task positions (relative to current list)."""
        filtered_tasks = self._get_sorted_filtered_tasks(self.incomplete_tasks_path)
        indices = self._convert_negatives(indices, len(filtered_tasks))
        convert_to_uuids = lambda idxs: {filtered_tasks[idx - 1].task_uuid for idx in idxs if 1 <= idx <= len(filtered_tasks)}
        tasks_to_delete_uuids = convert_to_uuids(indices)

        if not tasks_to_delete_uuids:
            print(f'No tasks found with the specified indices.')
            return
        
        self._delete_incomplete_tasks_by_uuid(tasks_to_delete_uuids, completing_tasks)

    
    def list_incomplete_tasks(self, verbose) -> None:
        """Print current tasks. Filters by current list with per-list indexing."""
        filtered_tasks = self._get_sorted_filtered_tasks(self.incomplete_tasks_path)

        print_format = PrintFormat.VERBOSE_REINDEXED if verbose else PrintFormat.SIMPLE_REINDEXED

        print(f'{self.current_list} *')
        self._print_tasks(filtered_tasks, print_format)

    
    def list_completed_tasks(self, n, show_all, verbose) -> None:
        """Print completed tasks. Filters by current list. By default, lists five most recently completed tasks."""
        filtered_tasks = self._get_sorted_filtered_tasks(self.completed_tasks_path)
        if not show_all:
            tasks_to_show = self._get_n_completed_tasks(filtered_tasks, n)
        
        print_format = PrintFormat.VERBOSE_REINDEXED if verbose else PrintFormat.SIMPLE_REINDEXED
        self._print_tasks(tasks_to_show, print_format)

    
    def view_log(self, show_all) -> None:
        """Print command log history. Defaults to five prior commands."""
        try:
            with open(self.log_file_path, 'r') as file:
                log = [line.strip() for line in file]
            log = log if show_all else log[-5:][::-1]
            for action in log:
                print(action)
        except FileNotFoundError:
            print("No log file found.")

    
    def pull(self) -> bool:
        """
        Pull encrypted files from Dropbox and merge with local files using intelligent merge logic.

        Variable naming schema:
        - D_ -> decrypted state.
        - P_ -> plaintext state
        """

        # TODO: Break into _pull and _merge methods.

        from .dropbox_sync import download_encrypted_files
        from .encryption import get_encryption_key
        
        key = get_encryption_key()
        if not key:
            print("Encryption password not set. Cannot pull from Dropbox.")
            return False
        
        download_ok = download_encrypted_files()
        if not download_ok:
            self._print_and_log("Failed to download encrypted files from Dropbox.")
            return False
        
        D_incomplete_tasks, err_msg_1 = self._load_tasks_from_encrypted(self.incomplete_tasks_path)
        D_completed_tasks, err_msg_2 = self._load_tasks_from_encrypted(self.completed_tasks_path)

        if err_msg_1 or err_msg_2:
            self._print_and_log(f"Failed to decrypt encrypted files. Error message: '{err_msg_1 if err_msg_1 else err_msg_2}'.")
            return False
        
        if D_incomplete_tasks is None and D_completed_tasks is None:
            self._print_and_log("No encrypted files found to synchronize with.")
            return False

        copy_tasks = lambda path: self._read_tasks(path) or self.tasks.copy()

        copy_incomplete_and_completed = lambda: (
            copy_tasks(self.incomplete_tasks_path),
            copy_tasks(self.completed_tasks_path)
        )

        P_incomplete_tasks, P_completed_tasks = copy_incomplete_and_completed()
        
        P_incomplete_by_uuid = {task.task_uuid: task for task in P_incomplete_tasks}
        P_completed_by_uuid = {task.task_uuid: task for task in P_completed_tasks}
        D_incomplete_by_uuid = {task.task_uuid: task for task in (D_incomplete_tasks or [])}
        D_completed_by_uuid = {task.task_uuid: task for task in (D_completed_tasks or [])}
        
        # 1. Any completed task in D that is currently incomplete in P -> complete it
        # 2. Any completed task in D that is not found in P -> add to P's completed tasks
        tasks_to_complete = []
        completed_tasks_to_add = []
        for D_task_uuid, D_complete_task in D_completed_by_uuid.items():
            assert D_task_uuid not in D_incomplete_by_uuid

            task_incomplete_in_P: bool = D_task_uuid in P_incomplete_by_uuid
            task_complete_in_P: bool = D_task_uuid in P_completed_by_uuid
            task_not_in_P: bool = (
                (D_task_uuid not in P_incomplete_by_uuid) and
                (D_task_uuid not in P_completed_by_uuid)
            )

            if task_incomplete_in_P:
                assert not task_complete_in_P
                self._print_and_log(f'Marking incomplete task as done: "{D_complete_task.text}".')
                tasks_to_complete.append(D_task_uuid)

            if task_not_in_P:
                self._print_and_log(f'Adding new completed task: "{D_complete_task.text}".')
                completed_tasks_to_add.append(D_complete_task)
        
        # 3. Any incomplete task in D that is not in P -> add to P's incomplete tasks
        incomplete_tasks_to_add = []
        for D_task_uuid, D_incomplete_task in D_incomplete_by_uuid.items():
            assert D_task_uuid not in D_completed_by_uuid

            task_not_in_P: bool = (
                (D_task_uuid not in P_incomplete_by_uuid) and
                (D_task_uuid not in P_completed_by_uuid)
            )

            if task_not_in_P:
                self._print_and_log(f'Adding new incomplete task: "{D_incomplete_task.text}".')
                incomplete_tasks_to_add.append(D_incomplete_task)
        
        # 4. Any incomplete task in D that is completed in P -> ignore

        if not tasks_to_complete and not completed_tasks_to_add and not incomplete_tasks_to_add:
            self._print_and_log("Local files are already up to date with Dropbox files.")
            return True

        if tasks_to_complete:
            # Directly complete tasks by UUID (bypassing index-based complete_tasks)
            tasks_to_complete_list = [P_incomplete_by_uuid[uuid_key] for uuid_key in tasks_to_complete]
            for task in tasks_to_complete_list:
                task.mark_end_time()
            P_completed_tasks.extend(tasks_to_complete_list)
            # Remove from incomplete
            P_incomplete_tasks = [task for task in P_incomplete_tasks if task.task_uuid not in tasks_to_complete]
            P_incomplete_tasks, P_completed_tasks = copy_incomplete_and_completed()
        
        if completed_tasks_to_add:
            P_completed_tasks.extend(completed_tasks_to_add)
        
        if incomplete_tasks_to_add:
            P_incomplete_tasks.extend(incomplete_tasks_to_add)

        self._write_tasks_to_file(self.incomplete_tasks_path, P_incomplete_tasks, 'w')
        self._write_completed_tasks_to_file(self.completed_tasks_path, P_completed_tasks, ensure_sort=True)
        
        self._print_and_log("Pulled tasks from Dropbox and merged with local files.")

        return True
    
    
    def push(self) -> bool:
        """Push encrypted files to Dropbox."""
        from .encryption import encrypt_file, get_encryption_key
        from .dropbox_sync import upload_encrypted_files
        
        key = get_encryption_key()
        if not key:
            print("Encryption password not set. Cannot push to Dropbox.")
            return False
        
        for file_path in TASK_FILES:
            encrypt_file(file_path)
        
        upload_ok = upload_encrypted_files()
        if not upload_ok:
            self._print_and_log("Failed to push encrypted files to Dropbox.")
            return False
        
        self._print_and_log("Pushed encrypted files to Dropbox.")
        return True
        
    
    def sync(self) -> None:
        """Synchronize with Dropbox: pull then push."""
        pull_ok = self.pull()
        if not pull_ok:
            self._print_and_log("Aborted synchronization with Dropbox due to failed pull.")
            return
        
        push_ok = self.push()
        if not push_ok:
            self._print_and_log("Aborted synchronization with Dropbox due to failed push.")
            return
        
        self._print_and_log("Successfully synchronized with Dropbox!")

    
    def show_lists(self) -> None:
        """Show all lists."""
        all_lists = self._get_all_lists()

        self._read_tasks(self.incomplete_tasks_path)
        counts = defaultdict(int)
        for task in self.tasks:
            if task.list_name is not None:
                counts[task.list_name] += 1
        counts[ALL_LIST_NAME] = len(self.tasks)

        longest_list_name = max(len(list_name) for list_name in all_lists) 
        for list_name in all_lists:
            key = list_name if list_name is not None else ALL_LIST_NAME
            padding = ' ' * (longest_list_name - len(list_name))
            value = counts[key] if key in counts else 0
            conditional_s: str = '' if value == 1 else 's'
            emphasize_current = '*' if list_name == self.current_list else ''
            print(f'{list_name}{padding} ({value} task{conditional_s}) {emphasize_current}')

    
    def create_list(self, list_name: str) -> None:
        """Create a new list."""
        list_name = list_name.upper()

        if list_name in RESERVED_LIST_NAMES:
            print(f'"{list_name}" is a reserved list name and cannot be created.')
            return
        
        existing_lists = self._get_all_lists()
        if list_name in existing_lists:
            print(f'List "{list_name}" already exists.')
            return
        
        add_additional_list(list_name)
        self._print_and_log(f'Created list "{list_name}".')

   
    def delete_list(self, list_name: str) -> None:
        """Delete a list and all of its tasks."""
        list_name = list_name.upper()

        if list_name in RESERVED_LIST_NAMES:
            print(f'"{list_name}" is a reserved list and cannot be deleted.')
            return
        
        existing_lists = self._get_all_lists()
        if list_name not in existing_lists:
            print(f'List "{list_name}" does not exist.')
            return
        
        self._read_tasks(self.incomplete_tasks_path)
        tasks_to_delete_uuids = {task.task_uuid for task in self.tasks if task.list_name == list_name}
        if tasks_to_delete_uuids:
            self._delete_incomplete_tasks_by_uuid(list(tasks_to_delete_uuids), completing_tasks=False)
        
        remove_additional_list(list_name)
        conditional_s: str = '' if len(tasks_to_delete_uuids) == 1 else 's'
        self._print_and_log(f'Deleted list "{list_name}" and {len(tasks_to_delete_uuids)} task{conditional_s}.')

  
    def checkout_list(self, list_name: str) -> None:
        """Switch to a different list."""
        list_name = list_name.upper()

        existing_lists = self._get_all_lists()
        if list_name not in existing_lists and list_name != ALL_LIST_NAME:
            print(f'List "{list_name}" does not exist. Please use `mtd -nl "{list_name}"` to create it.')
            return 

        set_current_list(list_name)
        self._print_and_log(f'Switched to list "{list_name}".')


    def _delete_incomplete_tasks_by_uuid(self, task_uuids_to_delete: list[Task], completing_tasks: bool) -> None:
        """Delete incomplete tasks based on supplied task UUIDs."""
        matching_tasks = [task for task in self.tasks if task.task_uuid in task_uuids_to_delete]
        remaining_tasks = [task for task in self.tasks if task.task_uuid not in task_uuids_to_delete]
        self._write_tasks_to_file(self.incomplete_tasks_path, remaining_tasks, 'w')

        if not completing_tasks:
            for task in matching_tasks:
                self._print_and_log(f'Deleted task "{task.text}".')

    
    def _get_all_lists(self) -> list[str]:
        """Get all list names from state file. Always includes 'All'."""
        res: list[str] = [ALL_LIST_NAME]

        additional_lists = get_additional_lists()

        self._read_tasks(self.incomplete_tasks_path)
        list_names = set()
        for task in self.tasks:
            if task.list_name is not None:
                list_names.add(task.list_name)

        assert list_names.issubset(additional_lists)

        res.extend(additional_lists)
        return res


    def _get_filtered_tasks_by_list(self) -> list[Task]:
        """Filter tasks by current list."""
        if self.current_list == ALL_LIST_NAME:
            return self.tasks
        
        return [task for task in self.tasks if task.list_name == self.current_list]


    def _get_sorted_filtered_tasks(self, path: str) -> list[Task]:
        """Read tasks from file and filter by list name."""
        self._read_tasks(path)
        return sorted(self._get_filtered_tasks_by_list(), key=lambda task: task.start_time)


    def _read_tasks(self, path: str) -> None:
        """Load incomplete or completed tasks to local memory."""
        tasks = []
        try:
            with open(path, 'r') as file:
                for line in file:
                    serialized_task = json.loads(line.strip())
                    task = Task.deserialize(serialized_task)
                    tasks.append(task)
                self.tasks = tasks
        except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError):
            return


    def _load_tasks_from_encrypted(self, path: str) -> tuple[Optional[list[Task]], Optional[str]]:
        """Load tasks from encrypted file into memory. Returns None if file doesn't exist or decryption fails."""
        from cryptography.fernet import Fernet, InvalidToken
        from .encryption import get_encryption_key
        
        key = get_encryption_key()
        if not key:
            return None, "Encryption password not set."
 
        encrypted_path = get_encrypted_file_path(path)
        if not os.path.exists(encrypted_path):
            return None, "Encrypted file not found."
        
        try:
            fernet = Fernet(key)
            with open(encrypted_path, 'rb') as f:
                encrypted = f.read()
            
            decrypted = fernet.decrypt(encrypted)
            
            tasks = []
            for line in decrypted.decode('utf-8').strip().split('\n'):
                if line.strip():
                    serialized_task = json.loads(line.strip())
                    task = Task.deserialize(serialized_task)
                    tasks.append(task)
            
            return tasks, None
        except InvalidToken:
            return None, "Invalid password."
        except Exception as e:
            return None, f"An unknown error occurred while decrypting the file: '{e}'."


    def _write_completed_tasks_to_file(self, path: str, tasks: list[Task], ensure_sort=False) -> None:
        """Write all tasks, either incomplete or complete, to appropriate file."""
        if ensure_sort:
            parse_timestamp = lambda ts: datetime.strptime(ts, '%H:%M %d-%m-%y') if isinstance(ts, str) else datetime.min

            is_sorted = all(parse_timestamp(tasks[i].end_time) <= parse_timestamp(tasks[i+1].end_time) for i in range(len(tasks) - 1))
            if not is_sorted:
                tasks.sort(key=lambda t: parse_timestamp(t.end_time))

        self._write_tasks_to_file(path, tasks, 'a')


    def _write_tasks_to_file(self, path: str, tasks: list[Task], open_param: str) -> None:
        to_write: list[dict] = [t.serialize() for t in tasks]
        with open(path, open_param) as file:
            for task in to_write:
                file.write(json.dumps(task) + '\n')


    def _convert_negatives(self, indices, length_of_current_tasks) -> list[int]:
        """Convert negative indices to their appropriate positive indices."""
        convert = lambda x: x if x >= 0 else length_of_current_tasks + x + 1
        indices = [convert(i) for i in indices]
        return indices


    def _get_n_completed_tasks(self, tasks, n) -> list[Task]:
        """Return slice of last `n` completed tasks."""
        return tasks[-n:] if n >= 0 else tasks[:abs(n)]


    def _print_and_log(self, message) -> None:
        """Write message to log file and print message as output."""
        with open(self.log_file_path, 'a') as file:
            file.write(f'{self.current_time.strftime("%H:%M %d-%m-%y")} | {message}\n')
        print(message)


    def _print_tasks(self, tasks: list[Task], print_format: PrintFormat) -> None:
        """
        Print passed-in tasks. Tasks should be pre-sorted deterministically.
        Indices are dynamically generated during display (1-indexed).
        """
        if not tasks:
            print("No tasks to show.")
            return
        
        for i, task in enumerate(tasks, start=1):
            match print_format:
                case PrintFormat.SIMPLE:
                    to_print = task.simple_to_string()
                case PrintFormat.SIMPLE_REINDEXED:
                    to_print = f'{i}. {task.simple_to_string()}'
                case PrintFormat.VERBOSE:
                    to_print = task.verbose_to_string()
                case PrintFormat.VERBOSE_REINDEXED:
                    to_print = f'{i}. {task.verbose_to_string()}'
            
            print(to_print)
