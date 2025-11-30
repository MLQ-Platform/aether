from pathlib import Path
import yaml


class DataSchema:
    """
    Data schema configuration loader for schema.yaml
    """

    def __init__(self, config_path: str = "config/schema.yaml"):
        self.config_path = Path(config_path)
        self.data_schema = self._load()

    def _load(self) -> dict:
        """
        Load schema.yaml
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.config_path}")

        with open(self.config_path) as f:
            return yaml.safe_load(f)

    def get_index_info(self) -> dict:
        """
        Get index column information
        """
        return self.data_schema.get("index", {})

    def get_description(self, with_index: bool = False) -> str:
        """
        Get human-readable description for LLM context
        """
        lines = ["Available Data Columns:"]

        columns = self.data_schema.get("columns", {})

        for col_name, col_info in columns.items():
            col_desc = col_info.get("description", "")
            col_type = col_info.get("type", "")
            lines.append(f"  - {col_name} ({col_type}): {col_desc}")

        if with_index:
            lines.append("\nIndex:")
            index_info = self.get_index_info()
            index_name = index_info.get("name", "")
            index_type = index_info.get("type", "")
            index_desc = index_info.get("description", "")
            lines.append(f"  - {index_name} ({index_type}): {index_desc}")

        return "\n".join(lines)
