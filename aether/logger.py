import logging
import sys
from typing import Optional


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    간단한 로거 생성 함수

    Args:
        name: 로거 이름 (보통 __name__)
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        logging.Logger: 설정된 로거 객체
    """
    logger = logging.getLogger(name)

    # 이미 핸들러가 있으면 중복 생성 방지
    if logger.handlers:
        return logger

    # 로그 레벨 설정
    logger.setLevel(getattr(logging, level.upper()))

    # 콘솔 핸들러 생성
    handler = logging.StreamHandler(sys.stdout)

    # 포매터 설정
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    # 핸들러를 로거에 추가
    logger.addHandler(handler)

    return logger
