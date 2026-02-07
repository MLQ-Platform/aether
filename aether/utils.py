import json
import uuid
from typing import List
from pydantic import BaseModel


def add_uuid(instances: List[BaseModel]):
    """
    Add a UUID to each instance in the list
    """
    valid_instances = [
        instance
        for instance in instances
        if instance is not None and not isinstance(instance, Exception)
    ]

    for instance in valid_instances:
        instance.uuid = generate_uuid()

    return valid_instances


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


def load_json(filepath: str) -> dict:
    """
    Load a JSON file
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


def save_json(data: dict, file_path: str):
    """
    Save a JSON file
    """
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return data
