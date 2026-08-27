import logging
from pathlib import Path


def get_logger() -> logging.Logger:
    """파일과 콘솔에 같은 형식으로 로그를 남긴다."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    logger = logging.getLogger("news_pipeline")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
    console_handler = logging.StreamHandler()
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger
