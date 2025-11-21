#!/usr/bin/env python3


from mtd.cli import get_parser, process_parser
from mtd.config import prepare_directory_and_files
from mtd.paths import COMPLETED_TASKS_FILE, INCOMPLETE_TASKS_FILE, LOG_FILE
from mtd.task_operator import TaskOperator


def main() -> None:
    prepare_directory_and_files()
    parser = get_parser()
    task_operator = TaskOperator(INCOMPLETE_TASKS_FILE, COMPLETED_TASKS_FILE, LOG_FILE)
    process_parser(parser, task_operator)


if __name__ == '__main__':
    main()
