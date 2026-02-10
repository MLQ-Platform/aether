from pathlib import Path

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def load_prompt(file_path: str, **variables) -> str:
    """Load a prompt template and substitute <<KEY>> variables."""
    path = Path(file_path)
    if not path.is_absolute():
        path = PROMPTS_DIR / path
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")

    content = path.read_text(encoding="utf-8")
    for key, value in variables.items():
        content = content.replace(f"<<{key}>>", str(value))
    return content.strip()
