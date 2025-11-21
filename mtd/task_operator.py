import json
import os
import uuid
from datetime import datetime
from typing import Optional

from .paths import TASK_FILES, get_encrypted_file_path
from .enums import PrintFormat, SortStrategy
from .task import Task


class TaskOperator:
    """
    Provides primary operations on tasks: Creating, deleting, reading, printing, et c.

    TaskOperator is instantiated once to complete tasks. It either reads data or reads AND writes data, then terminates. Each instance of TaskOperator performs a single action, and thus it does not juggle state as a user calls MTD repeatedly. When reading (to list incomplete or completed tasks), TaskOperator must deserialize the tasks from their .txt format first. When writing tasks, TaskOperator appends tasks through the their instantiated Task objects method `serialize`.
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

    def add_task(self, text, priority) -> None:
        """Write task to incomplete tasks file via appending, then print the updated task-list."""
        self._read_tasks(self.incomplete_tasks_path)
        next_index = len(self.tasks) + 1
        new_task = Task(text, next_index, priority)
        self.tasks.append(new_task)
        self._write_tasks_to_file(self.incomplete_tasks_path, self.tasks, 'w')

        self._print_and_log(f'Added task "{text}".')

    def complete_tasks(self, indices) -> None:
        """Complete all tasks based on supplied tasks' indices."""
        self._read_tasks(self.incomplete_tasks_path)
        indices = self._convert_negatives(indices, len(self.tasks))
        tasks = [task for task in self.tasks if task.index in indices]
        for task in tasks:
            task.mark_end_time()

        self._write_completed_tasks_to_file(self.completed_tasks_path, tasks)
        self.delete_incomplete_tasks(indices, completing_tasks=True)

        for task in tasks:
            self._print_and_log(f'Completed "{task.text}".')

    def delete_incomplete_tasks(self, indices, completing_tasks=False) -> None:
        """
        Delete tasks based on supplied tasks' indices. If tasks are not being deleted due to completion, print deletion confirmation messages. Only incomplete tasks may be deleted.
        """
        self._read_tasks(self.incomplete_tasks_path)
        indices = self._convert_negatives(indices, len(self.tasks))
        tasks_to_delete = [task for task in self.tasks if task.index in indices]
        remaining_tasks = [task for task in self.tasks if task.index not in indices]
        self._reindex_tasks(remaining_tasks)
        self._write_tasks_to_file(self.incomplete_tasks_path, remaining_tasks, 'w')

        if not completing_tasks:
            for task in tasks_to_delete:
                self._print_and_log(f'Deleted task "{task.text}".')

    def update_priority(self, index, priority) -> None:
        """
        Update the priority of a task via a specified task index and a new priority.
        """
        if priority not in range(0, 5):
            print("Please choose a priority between 1 and 4, or choose 0 to remove.")
            return
        else:
            self._read_tasks(self.incomplete_tasks_path)
            task_to_update = next((task for task in self.tasks if task.index == index), None)
            if task_to_update and task_to_update.priority != priority:
                task_to_update.priority = priority
                self._write_tasks_to_file(self.incomplete_tasks_path, self.tasks, 'w')
                self._print_and_log(f'Set priority of "{task_to_update.text}" to {priority}.')
            elif task_to_update and task_to_update.priority == priority:
                print(f'Task priority was already set as {priority}.')
            else:
                print(f'No task exists with index {index}.')

    def list_incomplete_tasks(self, priority_sort, verbose) -> None:
        """Print current tasks. Always prints all incomplete tasks."""
        self._read_tasks(self.incomplete_tasks_path)
        sort_strategy = SortStrategy.PRIORITY_THEN_INDEX if priority_sort else SortStrategy.INDEX_ASCENDING
        print_format = PrintFormat.VERBOSE if verbose else PrintFormat.SIMPLE
        self._print_tasks(self.tasks, sort_strategy, print_format)

    def list_completed_tasks(self, n, show_all, priority_sort, verbose) -> None:
        """Print completed tasks. By default, lists five most recently completed tasks."""
        self._read_tasks(self.completed_tasks_path)
        tasks_to_show = self.tasks
        if not show_all:
            tasks_to_show = self._get_n_completed_tasks(tasks_to_show, n)
        reverse = n > 0 and not show_all
        
        if priority_sort:
            sort_strategy = SortStrategy.PRIORITY_THEN_INDEX_REVERSED if reverse else SortStrategy.PRIORITY_THEN_INDEX
        else:
            sort_strategy = SortStrategy.INDEX_DESCENDING if reverse else SortStrategy.INDEX_ASCENDING
        
        print_format = PrintFormat.VERBOSE_REINDEXED if verbose else PrintFormat.SIMPLE_REINDEXED
        
        self._print_tasks(tasks_to_show, sort_strategy, print_format)

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
            indices_to_complete = [P_incomplete_by_uuid[uuid_key].index for uuid_key in tasks_to_complete]
            self.complete_tasks(indices_to_complete)
            P_incomplete_tasks, P_completed_tasks = copy_incomplete_and_completed()
        
        if completed_tasks_to_add:
            P_completed_tasks.extend(completed_tasks_to_add)
        
        if incomplete_tasks_to_add:
            P_incomplete_tasks.extend(incomplete_tasks_to_add)
            self._reindex_tasks(P_incomplete_tasks)

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


    def _read_tasks(self, path: str) -> None:
        """Load incomplete or completed tasks to local memory."""
        tasks = []
        try:
            with open(path, 'r') as file:
                for line in file:
                    serialized_task = json.loads(line.strip())
                    task = Task.deserialize(serialized_task)
                    # Ensure UUID exists for backward compatibility
                    if not hasattr(task, 'task_uuid') or not task.task_uuid:
                        task.task_uuid = str(uuid.uuid4())
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
                    # Ensure UUID exists for backward compatibility
                    if not hasattr(task, 'task_uuid') or not task.task_uuid:
                        task.task_uuid = str(uuid.uuid4())
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

    def _reindex_tasks(self, tasks) -> None:
        """Reindex all tasks, starting from 1."""
        if not tasks:
            return

        index = 1
        for task in tasks:
            task.index = index
            index += 1

    def _get_n_completed_tasks(self, tasks, n) -> list[Task]:
        """Return slice of last `n` completed tasks."""
        return tasks[-n:] if n >= 0 else tasks[:abs(n)]

    def _print_and_log(self, message) -> None:
        """Write message to log file and print message as output."""
        with open(self.log_file_path, 'a') as file:
            file.write(f'{self.current_time.strftime("%H:%M %d-%m-%y")} | {message}\n')
        print(message)

    def _print_tasks(self, tasks, sort_strategy: SortStrategy, print_format: PrintFormat) -> None:
        """
        Print passed-in tasks which may differ from those in memory.
        """
        if not tasks:
            print("No tasks to show.")
            return

        sorted_tasks = self._preprint_sort(tasks, sort_strategy)
        
        for i, task in enumerate(sorted_tasks, start=1):
            match print_format:
                case PrintFormat.SIMPLE:
                    to_print = task.simple_to_string()
                case PrintFormat.SIMPLE_REINDEXED:
                    to_print = f'{i}. ' + task.simple_to_string(with_index=False)
                case PrintFormat.VERBOSE:
                    to_print = task.verbose_to_string()
                case PrintFormat.VERBOSE_REINDEXED:
                    to_print = f'{i}. ' + task.verbose_to_string(with_index=False)
            
            print(to_print)

    def _preprint_sort(self, tasks, sort_strategy: SortStrategy) -> list[Task]:
        """
        Sort tasks according to the specified strategy.
        """
        match sort_strategy:
            case SortStrategy.INDEX_ASCENDING:
                return sorted(tasks, key=lambda x: x.index)
            case SortStrategy.INDEX_DESCENDING:
                return sorted(tasks, key=lambda x: x.index, reverse=True)
            case SortStrategy.PRIORITY_THEN_INDEX:
                return sorted(tasks, key=lambda x: [x.priority, -x.index], reverse=True)
            case SortStrategy.PRIORITY_THEN_INDEX_REVERSED:
                return list(
                    sorted(tasks, key=lambda x: [x.priority, -x.index], reverse=False)
                )
            case _:
                raise ValueError(f"Invalid sort strategy: {sort_strategy}")
