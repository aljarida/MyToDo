from enum import Enum


class SortStrategy(Enum):
    """Enumeration for task sorting strategies."""
    INDEX_ASCENDING = "index_ascending"
    INDEX_DESCENDING = "index_descending"
    PRIORITY_THEN_INDEX = "priority_then_index"
    PRIORITY_THEN_INDEX_REVERSED = "priority_then_index_reversed"


class PrintFormat(Enum):
    """Enumeration for task printing formats."""
    SIMPLE = "simple"
    SIMPLE_REINDEXED = "simple_reindexed"
    VERBOSE = "verbose"
    VERBOSE_REINDEXED = "verbose_reindexed"


class Help(Enum):
    """Help text for CLI arguments."""
    LIST = 'list -> list currently active tasks'
    PRIORITY_SORT = 'priority sort -> combine with -l to sort tasks by priority'
    LIST_COMPLETED = 'list completed -> list completed tasks (most recent 5 by default); specify a positive or negative integer n for nth most recent or historic entries'
    VIEW_LOG = 'view log -> view previous additions, deletions, and completions (most recent 5 by default)'
    SHOW_ALL = 'show all -> combine with -lc to show all completed tasks or -vl to show all logged edits'
    VERBOSE = 'verbose -> combine with -l or -lc to list tasks in verbose fashion'
    ADD = 'add -> add a new task'
    PRIORITY = 'priority -> combine with -a to set a priority between 1 and 4 --- e.g., `-a "task" -p 2`'
    DELETE = 'delete -> delete one or more tasks by index'
    COMPLETE = 'complete -> complete one or more tasks by index'
    UPDATE_PRIORITY = 'set priority -> update task\'s priority by integer index with new priority'
    PULL = 'pull -> pull encrypted files from Dropbox and merge with local files'
    PUSH = 'push -> push encrypted files to Dropbox'
    SYNCHRONIZE = 'synchronize -> pull encrypted files from Dropbox, merge with local files, then push back to Dropbox'