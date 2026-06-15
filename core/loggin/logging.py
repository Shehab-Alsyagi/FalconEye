"""
============================================================
LOGGING CONFIGURATION
============================================================
"""

import logging
from pathlib import Path
from datetime import datetime
from core.config.settings import settings


def setup_logging(name: str = "Logs System") -> logging.Logger:
    """
    Args:
        name:  logger name (optional)

    Returns:
        logging.Logger: logger object 
    """
    log_dir = settings.LOGS_DIR
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"ingestion_{datetime.now().strftime('%Y%m%d')}.log"

    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format=settings.LOG_FORMAT,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler() 
        ]
    )
    logger_name = name if name else __name__
    logger = logging.getLogger(logger_name)

    return logger

default_logger = setup_logging("ingestion_system")
