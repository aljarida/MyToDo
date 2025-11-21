import argparse

from .enums import Help
from .task_operator import TaskOperator


def get_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(prog='mtd', description='Manage your to-do list.')

    def add_list_commands(parser) -> None:
        parser.add_argument('-l', '--list', action='store_true', dest='l', help=Help.LIST.value)
        parser.add_argument('-ps', '--priority-sort', action='store_true', dest='ps', help=Help.PRIORITY_SORT.value)
        parser.add_argument('-lc', '--list-completed', nargs='?', type=int, dest='lc', const=5, help=Help.LIST_COMPLETED.value)
        parser.add_argument('-vl', '--view-log', action='store_true', dest='vl', help=Help.VIEW_LOG.value)
        parser.add_argument('-sa', '--show-all', action='store_true', dest='sa', help=Help.SHOW_ALL.value)
        parser.add_argument('-v', '--verbose', action='store_true', dest='v', help=Help.VERBOSE.value)

    def add_edit_commands(parser) -> None:
        parser.add_argument('-a', '--add', nargs=1, type=str, dest='a', help=Help.ADD.value)
        parser.add_argument('-p', '--priority', type=int, choices=[1, 2, 3, 4], default=0, dest='p', help=Help.PRIORITY.value)
        parser.add_argument('-d', '--delete', nargs='+', type=int, dest='d', help=Help.DELETE.value)
        parser.add_argument('-c', '--complete', nargs='+', type=int, dest='c', help=Help.COMPLETE.value)
        parser.add_argument('-up', '--update-priority', '-sp', nargs=2, type=int, dest='up', help=Help.UPDATE_PRIORITY.value)
        parser.add_argument('--pull', action='store_true', dest='pull', help=Help.PULL.value)
        parser.add_argument('--push', action='store_true', dest='push', help=Help.PUSH.value)
        parser.add_argument('-s', '--synchronize', action='store_true', dest='sync', help=Help.SYNCHRONIZE.value)
    
    add_list_commands(parser)
    add_edit_commands(parser)
    
    return parser


def process_parser(parser: argparse.ArgumentParser, task_operator: TaskOperator) -> None:
    """Process parsed arguments and execute corresponding task operations."""
    args = parser.parse_args()

    if args.l:
        task_operator.list_incomplete_tasks(args.ps, args.v)
    elif args.lc:
        task_operator.list_completed_tasks(n=args.lc, show_all=args.sa, priority_sort=args.ps, verbose=args.v)
    elif args.vl:
        task_operator.view_log(show_all=args.sa)
    elif args.pull:
        task_operator.pull()
    elif args.push:
        task_operator.push()
    elif args.sync:
        task_operator.sync()
    elif args.a:
        task_operator.add_task(args.a[0], args.p)
    elif args.d:
        task_operator.delete_incomplete_tasks(args.d)
    elif args.c:
        task_operator.complete_tasks(args.c)
    elif args.up:
        task_operator.update_priority(args.up[0], args.up[1])
    else:
        parser.print_help()

