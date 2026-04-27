# wallasAPI/logger.py
"""
Centralized logging for the wallasAPI package.
All modules should use `from .logger import log` instead of print().
"""
import logging
import sys

def setup_logger(name: str = "wallasAPI", level: int = logging.INFO) -> logging.Logger:
    """Creates and returns a configured logger for the package."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(level)
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s | %(message)s",
            datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

# Singleton logger instance for the whole package
log = setup_logger()
