import uuid
from datetime import datetime


class Task:
    """
    Represents a task. Contains text, creation time, end time, and any associate list name.

    Includes methods for generating timestamps, string representations for printing (simple and verbose), and serialization.
    """
    def __init__(self, text: str, start_time='', end_time='', task_uuid='', list_name=None) -> None:
        """Initialize the task. All fields optional but text."""
        self.text: str = text
        self.start_time: str = Task.generate_timestamp() if start_time == '' else start_time
        self.end_time: str = end_time
        self.task_uuid: str = task_uuid if task_uuid else str(uuid.uuid4())
        self.list_name: str | None = list_name


    def mark_end_time(self) -> None:
        """Set the `end_time`."""
        self.end_time = Task.generate_timestamp()


    def simple_to_string(self) -> str:
        """Return a simple string representation of the task."""
        return self.text


    def verbose_to_string(self) -> str:
        """Return a verbose string representation of the task."""
        string_builder = []
        string_builder.append(f'Task: {self.text}')
        if self.start_time:
            string_builder.append(f'Start Time: {self.start_time}')
        if self.end_time:
            string_builder.append(f'End Time: {self.end_time}')
        return ' - '.join(string_builder)


    def serialize(self) -> dict:
        """Serialize the task for storage."""
        return self.__dict__


    @staticmethod 
    def deserialize(d: dict) -> "Task":
        """Returns a Task object from a dictionary."""
        return Task(**d)


    @staticmethod
    def generate_timestamp() -> str:
        """Generate a timestamp based on current time, precise to the minute."""
        return datetime.now().strftime('%H:%M %y-%m-%d')


    def __repr__(self) -> str:
        finished: str = 'COMPLETE' if self.end_time else 'INCOMPLETE'
        return f"Task({self.simple_to_string()}, {finished})"
