#!/usr/bin/env python3

import argparse
import json
import os
import sys

from datetime import datetime

HELP_LIST = 'list -> list currently active tasks'
HELP_PRIORITY_SORT = 'priority sort -> combine with -l to sort tasks by priority'
HELP_LIST_COMPLETED = 'list completed -> list completed tasks (most recent 5 by default); specify a positive or negative integer n for nth most recent or historic entries'
HELP_VIEW_LOG = 'view log -> view previous additions, deletions, and completions (most recent 5 by default)'
HELP_SHOW_ALL = 'show all -> combine with -lc to show all completed tasks or -vl to show all logged edits'
HELP_VERBOSE = 'verbose -> combine with -l or -lc to list tasks in verbose fashion'

HELP_ADD = 'add -> add a new task'
HELP_PRIORITY = 'priority -> combine with -a to set a priority between 1 and 4 --- e.g., `-a "task" -p 2`'
HELP_DELETE = 'delete -> delete one or more tasks by index'
HELP_COMPLETE = 'complete -> complete one or more tasks by index'
HELP_UPDATE_PRIORITY = 'set priority -> update task\'s priority by integer index with new priority'

SCRIPT_DIR: str = os.path.dirname(os.path.realpath(sys.argv[0]))
DATA_DIR: str = os.path.join(SCRIPT_DIR, '.mtd')
INCOMPLETE_TASKS_FILE: str = os.path.join(DATA_DIR, 'tasks.json')
COMPLETED_TASKS_FILE: str = os.path.join(DATA_DIR, 'completed_tasks.json')
LOG_FILE: str = os.path.join(DATA_DIR, 'log_file.txt')


class Task():
    """
    Represents a task. Contains text, index, creation time, and finish time.

    Includes methods for generating timestamps, string representations for printing (simple and verbose), and serialization.
    """
    def __init__(self, text: str, index=0, priority=0, start_time='', end_time='') -> None:
        """Initialize the task. All fields optional but text."""
        self.text: str = text
        self.index: int = index
        self.priority: int = priority
        self.start_time: str = Task.generate_timestamp() if start_time == '' else start_time
        self.end_time: str = end_time


    def mark_end_time(self) -> None:
        """Set the `end_time`."""
        self.end_time = Task.generate_timestamp()

    def simple_to_string(self, with_index=True) -> str:
        """Return a simple string representation of the task."""
        string_builder = []
        if with_index and self.index: string_builder.append(f'{self.index}.')
        if self.priority: string_builder.append(f'*P{self.priority}*')
        string_builder.append(f'{self.text}')
        return ' '.join(string_builder)

    def verbose_to_string(self, with_index=True) -> str:
        """Return a verbose string representation of the task."""
        string_builder = []
        if with_index and self.index: string_builder.append(f'Index: {self.index}')
        if self.priority: string_builder.append(f'Priority: {self.priority}')
        string_builder.append(f'Task: {self.text}')
        if self.start_time: string_builder.append(f'Start Time: {self.start_time}')
        if self.end_time: string_builder.append(f'End Time: {self.end_time}')
        return ' - '.join(string_builder)

    def serialize(self) -> dict:
        """Seralize the task for storage."""
        return self.__dict__
   
    @staticmethod 
    def deserialize(d: dict) -> "Task":
        """Returns a Task object from dictionary."""
        return Task(**d)

    @staticmethod
    def generate_timestamp() -> str:
        """Generate a timestamp based on current time, precise to the minute."""
        return datetime.now().strftime('%H:%M %y-%m-%d')


class TaskOperator():
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

    def read_tasks(self, path: str) -> None:
        """Load incomplete or completed tasks to local memory."""
        tasks = []
        try:
            with open(path, 'r') as file:
                for line in file:
                    serialized_task = json.loads(line.strip())
                    task = Task.deserialize(serialized_task)
                    tasks.append(task)
                self.tasks = tasks
        except: return

    def write_tasks_to_file(self, path: str, tasks: list[Task], open_param: str) -> None:
        """Write all tasks, either incomplete or complete, to appropriate file."""
        to_write: list[dict] = [t.serialize() for t in tasks]
        with open(path, open_param) as file:
            for task in to_write:
                file.write(json.dumps(task) + '\n')

    def add_task(self, text, priority) -> None:
        """Write task to incomplete tasks file via appending, then print the updated task-list."""
        self.read_tasks(self.incomplete_tasks_path)
        next_index = len(self.tasks) + 1
        new_task = Task(text, next_index, priority)
        self.tasks.append(new_task)
        self.write_tasks_to_file(self.incomplete_tasks_path, self.tasks, 'w')

        self.print_and_log(f'Added task "{text}".')

    def convert_negatives(self, indices, length_of_current_tasks):
        """Convert negative indices to their appropriate positive indices."""
        convert = lambda x: x if x >= 0 else length_of_current_tasks + x + 1
        indices = [convert(i) for i in indices]
        return indices

    def complete_tasks(self, indices) -> None:
        """Complete all tasks based on supplied tasks' indices."""
        self.read_tasks(self.incomplete_tasks_path)
        indices = self.convert_negatives(indices, len(self.tasks))
        tasks = [task for task in self.tasks if task.index in indices]
        for task in tasks:
            task.mark_end_time()
        self.write_tasks_to_file(self.completed_tasks_path, tasks, 'a')
        self.delete_tasks(indices, completing_tasks=True)

        for task in tasks:
            self.print_and_log(f'Completed "{task.text}".')

    def delete_tasks(self, indices, completing_tasks=False) -> None:
        """
        Delete tasks based on supplied tasks' indices. If tasks are not being deleted due to completion, print deletion confirmation messages. Only incomplete tasks may be deleted.
        """
        self.read_tasks(self.incomplete_tasks_path)
        indices = self.convert_negatives(indices, len(self.tasks))
        tasks_to_delete = [task for task in self.tasks if task.index in indices]
        remaining_tasks = [task for task in self.tasks if task.index not in indices]
        self.reindex_tasks(remaining_tasks)
        self.write_tasks_to_file(self.incomplete_tasks_path, remaining_tasks, 'w')

        if not completing_tasks:
            for task in tasks_to_delete:
                self.print_and_log(f'Deleted task "{task.text}".')

    def update_priority(self, index, priority) -> None:
        """
        Update the priority of a task via a specified task index and a new priority.
        """
        if priority not in range(0,5):
            print("Please choose a priority between 1 and 4, or choose 0 to remove.")
            return
        else:
            self.read_tasks(self.incomplete_tasks_path)
            task_to_update = next((task for task in self.tasks if task.index == index), None)
            if task_to_update and task_to_update.priority != priority:
                task_to_update.priority = priority
                self.write_tasks_to_file(self.incomplete_tasks_path, self.tasks, 'w')
                self.print_and_log(f'Set priority of "{task_to_update.text}" to {priority}.')
            elif task_to_update and task_to_update.priority == priority:
                print(f'Task priority was already set as {priority}.')
            else:
                print(f'No task exists with index {index}.')

    def reindex_tasks(self, tasks) -> None:
        """Reindex all tasks, starting from 1."""
        if not tasks: return
        index = 1
        for task in tasks:
            task.index = index
            index += 1

    def list_incomplete_tasks(self, priority_sort, verbose) -> None:
        """Print current tasks. Always prints all incomplete tasks."""
        self.read_tasks(self.incomplete_tasks_path)
        self.print_tasks(self.tasks, priority_sort, verbose)

    def list_completed_tasks(self, n, show_all, priority_sort, verbose) -> None:
        """Print completed tasks. By default, lists five most recently completed tasks."""
        self.read_tasks(self.completed_tasks_path)
        tasks_to_show = self.tasks
        if not show_all:
            tasks_to_show = self.get_n_completed_tasks(tasks_to_show, n)
        reverse = n > 0 and not show_all
        self.print_tasks(tasks_to_show, priority_sort, verbose, reverse=reverse, reindex=True)

    def get_n_completed_tasks(self, tasks, n) -> list[Task]:
        """Return slice of last `n` completed tasks."""
        return tasks[-n:] if n >=0 else tasks[:abs(n)]

    def view_log(self, show_all) -> None:
        """Print command log history. Defaults to five prior commands."""
        with open(self.log_file_path, 'r') as file:
            log = [line.strip() for line in file]
        log = log if show_all else log[-5:][::-1]
        for action in log:
            print(action)

    def print_and_log(self, message) -> None:
        """Write message to log file and print message as output."""
        with open(self.log_file_path, 'a') as file:
            file.write(message + '\n')
        print(message)

    def print_tasks(self, tasks, priority_sort: bool, verbose: bool, reverse=False, reindex=False) -> None:
        """
        Print passed-in tasks which may differ from those in memory. Specify whether the tasks should be sorted by priority, should be printed verbose, and whether reversal or re-indexing is needed.
        """
        if not tasks:
            print("No tasks to show.")
            return

        sorted_tasks = self.preprint_sort(tasks, priority_sort, reverse)
        for i, task in enumerate(sorted_tasks, start=1):
            if verbose and reindex:
                to_print = f'{i}. ' + task.verbose_to_string(with_index=False)
            elif verbose and not reindex:
                to_print = task.verbose_to_string()
            elif not verbose and reindex:
                to_print = f'{i}. ' + task.simple_to_string(with_index=False)
            else: # not verbose and not reindex
                to_print = task.simple_to_string()

            print(to_print)

    def preprint_sort(self, tasks, priority_sort, reverse=False) -> list[Task]:
        if priority_sort: # Sort such that first in line is highest priority, lowest index.
            tasks = sorted(tasks, key=lambda x: [x.priority, -x.index], reverse=True)
        else:             # Sort such that first in line is lowest index.
            tasks = sorted(tasks, key=lambda x: x.index)
        return tasks[::-1] if reverse else tasks


def prepare_directory_and_files() -> None:
    """Create hidden .mtd folder and tasks/log files only if they do not already exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    for file in [INCOMPLETE_TASKS_FILE, COMPLETED_TASKS_FILE, LOG_FILE]:
        if not os.path.exists(file):
            with open(file, 'w') as _: pass

def main() -> None:
    """
    Drive program by making needed folder/files, create parser, use TaskOperator to execute in response to user's chosen commands.
    """
    prepare_directory_and_files()

    parser = argparse.ArgumentParser(prog='mtd', description='Manage your to-do list.')

    # List commands:
    parser.add_argument('-l', '--list', action='store_true', dest='l', help=HELP_LIST)
    parser.add_argument('-ps', '--priority-sort', action='store_true', dest='ps', help=HELP_PRIORITY_SORT)
    parser.add_argument('-lc', '--list-completed', nargs='?', type=int, dest='lc', const=5, help=HELP_LIST_COMPLETED)
    parser.add_argument('-vl', '--view-log', action='store_true', dest='vl', help=HELP_VIEW_LOG)
    parser.add_argument('-sa', '--show-all', action='store_true', dest='sa', help=HELP_SHOW_ALL)
    parser.add_argument('-v', '--verbose', action='store_true', dest='v', help=HELP_VERBOSE)

    # Edit commands:
    parser.add_argument('-a', '--add', nargs=1, type=str, dest='a', help=HELP_ADD)
    parser.add_argument('-p', '--priority', type=int, choices=[1, 2, 3, 4], default=0, dest='p', help=HELP_PRIORITY)
    parser.add_argument('-d', '--delete', nargs='+', type=int, dest='d', help=HELP_DELETE)
    parser.add_argument('-c', '--complete', nargs='+', type=int, dest='c', help=HELP_COMPLETE)
    parser.add_argument('-up', '--update-priority', '-sp', nargs=2, type=int, dest='up', help=HELP_UPDATE_PRIORITY)

    args = parser.parse_args()
    operator = TaskOperator(INCOMPLETE_TASKS_FILE, COMPLETED_TASKS_FILE, LOG_FILE)

    if args.l:
        operator.list_incomplete_tasks(args.ps, args.v)
    elif args.lc:
        operator.list_completed_tasks(n=args.lc, show_all=args.sa, priority_sort=args.ps, verbose=args.v)
    elif args.vl:
        operator.view_log(show_all=args.sa)
    elif args.a:
        operator.add_task(args.a[0], args.p)
    elif args.d:
        operator.delete_tasks(args.d)
    elif args.c:
        operator.complete_tasks(args.c)
    elif args.up:
        operator.update_priority(args.up[0], args.up[1])
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
