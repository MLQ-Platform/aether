import sys
from loguru import logger

# 기본 핸들러 제거
logger.remove()
# 핸들러 추가
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{extra[name]}</cyan> : <level>{message}</level>",
    level="DEBUG",
    colorize=True,
)


def get_logger(name: str, level: str = "INFO"):
    """
    Loguru 기반 로거 생성 함수
    """
    return logger.bind(name=name)
