import argparse

from .enums import Help
from .task_operator import TaskOperator


def get_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(prog='mtd', description='Manage your to-do list.')

    def add_list_commands(parser) -> None:
        parser.add_argument('-l', '--list', action='store_true', dest='l', help=Help.LIST.value)
        parser.add_argument('-lc', '--list-completed', nargs='?', type=int, dest='lc', const=5, help=Help.LIST_COMPLETED.value)
        parser.add_argument('-vl', '--view-log', action='store_true', dest='vl', help=Help.VIEW_LOG.value)
        parser.add_argument('-sa', '--show-all', action='store_true', dest='sa', help=Help.SHOW_ALL.value)
        parser.add_argument('-v', '--verbose', action='store_true', dest='v', help=Help.VERBOSE.value)

    def add_edit_commands(parser) -> None:
        parser.add_argument('-a', '--add', nargs=1, type=str, dest='a', help=Help.ADD.value)
        parser.add_argument('-d', '--delete', nargs='+', type=int, dest='d', help=Help.DELETE.value)
        parser.add_argument('-c', '--complete', nargs='+', type=int, dest='c', help=Help.COMPLETE.value)
        parser.add_argument('--pull', action='store_true', dest='pull', help=Help.PULL.value)
        parser.add_argument('--push', action='store_true', dest='push', help=Help.PUSH.value)
        parser.add_argument('-s', '--synchronize', action='store_true', dest='sync', help=Help.SYNCHRONIZE.value)
    
    def add_list_management_commands(parser) -> None:
        parser.add_argument('-cl', '--checkout-list', nargs=1, type=str, dest='cl', help=Help.CHECKOUT_LIST.value)
        parser.add_argument('-sl', '--show-lists', action='store_true', dest='sl', help=Help.SHOW_LISTS.value)
        parser.add_argument('-dl', '--delete-list', nargs=1, type=str, dest='dl', help=Help.DELETE_LIST.value)
        parser.add_argument('-nl', '--new-list', nargs=1, type=str, dest='nl', help=Help.NEW_LIST.value)
    
    add_list_commands(parser)
    add_edit_commands(parser)
    add_list_management_commands(parser)
    
    return parser


def process_parser(parser: argparse.ArgumentParser, task_operator: TaskOperator) -> None:
    """Process parsed arguments and execute corresponding task operations."""
    args = parser.parse_args()

    if args.l:
        task_operator.list_incomplete_tasks(args.v)
    elif args.lc:
        task_operator.list_completed_tasks(n=args.lc, show_all=args.sa, verbose=args.v)
    elif args.vl:
        task_operator.view_log(show_all=args.sa)
    elif args.pull:
        task_operator.pull()
    elif args.push:
        task_operator.push()
    elif args.sync:
        task_operator.sync()
    elif args.a:
        task_operator.add_task(args.a[0])
    elif args.d:
        task_operator.delete_incomplete_tasks_by_indices(args.d)
    elif args.c:
        task_operator.complete_tasks(args.c)
    elif args.cl:
        task_operator.checkout_list(args.cl[0])
    elif args.sl:
        task_operator.show_lists()
    elif args.dl:
        task_operator.delete_list(args.dl[0])
    elif args.nl:
        task_operator.create_list(args.nl[0])
    else:
        parser.print_help()

