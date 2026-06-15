"""
============================================================
LOGGING CONFIGURATION
============================================================
تسجيل موحد للنظام بأكمله
"""

import logging
from pathlib import Path
from datetime import datetime
from core.config.settings import settings


def setup_logging(name: str = "Logs System") -> logging.Logger:
    """
    إعداد نظام التسجيل الموحد

    Args:
        name: اسم المسجل (اختياري)

    Returns:
        logging.Logger: كائن المسجل
    """
    log_dir = settings.LOGS_DIR
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"ingestion_{datetime.now().strftime('%Y%m%d')}.log"

    # تكوين أساسي
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format=settings.LOG_FORMAT,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # طباعة على الشاشة أيضاً
        ]
    )

    # إنشاء المسجل
    logger_name = name if name else __name__
    logger = logging.getLogger(logger_name)

    return logger


# مسجل افتراضي للنظام
default_logger = setup_logging("ingestion_system")
