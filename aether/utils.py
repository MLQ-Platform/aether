import uuid
from typing import List
from pydantic import BaseModel


def add_uuid(instances: List[BaseModel]):
    """
    Add a UUID to each instance in the list
    """
    for instance in instances:
        instance.uuid = generate_uuid()
    return instances


def generate_uuid() -> int:
    """
    Generate a unique UUID as integer
    """
    return int(str(uuid.uuid4())[:8], 16)


def generate_task_id() -> str:
    """
    Generate a unique task ID
    """
    return str(uuid.uuid4())[:3]
