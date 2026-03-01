import json
import os
import uuid
from datetime import datetime
from secrets import token_hex
from aether.exceptions import DataError


def timestamp_ymdhms() -> str:
    """
    Return current local time in YYYYMMDDHHMMSS.
    """
    return datetime.now().strftime("%Y%m%d%H%M%S")


def generate_id_tag(length: int = 8) -> str:
    """
    Generate a short random hex id tag.
    """
    return token_hex(max(1, length // 2))[:length]


def generate_task_id() -> str:
    """
    Generate a unique task ID
    """
    return token_hex(2)[:3]


def uuid_savepath(basedir: str, prefix: str) -> str:
    while True:
        base = f"{prefix}-{uuid.uuid4().hex[:8]}"
        path = os.path.join(basedir, f"{base}.json")
        if not os.path.exists(path):
            return path


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
