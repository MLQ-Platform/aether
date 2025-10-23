from pathlib import Path
from typing import Dict
from typing import Optional

# 패키지 내부 prompts 디렉토리 경로
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class PromptLoader:
    """
    프롬프트 로드
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Args:
            base_path: 프롬프트 파일 기본 경로 (없으면 aether/prompts)
        """
        self.base_path = Path(base_path) if base_path else PROMPTS_DIR

    def load(self, file_path: str, **variables) -> str:
        """
        프롬프트 로드

        Args:
            file_path: 텍스트 파일 경로 (aether/prompts 기준 상대경로 또는 절대경로)
            **variables: 템플릿 변수 (예: tree_structure="...", node_descriptions="...")
        """

        path = self._resolve_path(file_path)
        content = path.read_text(encoding="utf-8")

        # 변수 치환
        if variables:
            content = self._substitute_variables(content, variables)

        return content.strip()

    def _resolve_path(self, file_path: str) -> Path:
        """
        파일 경로 해석
        """
        path = Path(file_path)

        if path.is_absolute():
            return path

        # base_path 기준 상대 경로
        full_path = self.base_path / path

        if not full_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {full_path}")

        return full_path

    def _substitute_variables(self, content: str, variables: Dict[str, str]) -> str:
        """
        템플릿 변수 치환
        """
        for key, value in variables.items():
            content = content.replace(f"<<{key}>>", str(value))

        return content


def load_prompt(file_path: str, **variables) -> str:
    """
    프롬프트 로드
    """
    prompt_loader = PromptLoader()
    return prompt_loader.load(file_path, **variables)
