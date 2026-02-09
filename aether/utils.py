import json
import uuid
from typing import List
from pydantic import BaseModel
from aether.exceptions import DataError
from aether.logger import get_logger

logger = get_logger(__name__)


def add_uuid(instances: List[BaseModel]):
    """
    Add a UUID to each instance in the list
    """
    valid_instances = [
        instance
        for instance in instances
        if instance is not None and not isinstance(instance, Exception)
    ]

    dropped = len(instances) - len(valid_instances)
    if dropped > 0:
        logger.warning(
            f"add_uuid: filtered out {dropped}/{len(instances)} invalid instances"
        )

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
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError as e:
        raise DataError(f"JSON file not found: {filepath}") from e
    except json.JSONDecodeError as e:
        raise DataError(f"Invalid JSON in file: {filepath}") from e

    return data


def save_json(data: dict, file_path: str):
    """
    Save a JSON file
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError as e:
        raise DataError(f"Failed to write JSON file: {file_path}") from e
    except TypeError as e:
        raise DataError(f"Data is not JSON-serializable for file: {file_path}") from e

    return data
