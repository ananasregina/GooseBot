import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler

def setup_logger(
    name: str = "goosebot",
    log_file: Optional[Path] = None,
    level: int = logging.DEBUG,
    extra_handlers: Optional[list] = None,
    **kwargs  # Absorb any remaining arguments
) -> logging.Logger:
    """Set up and return a logger instance. Console output is DISABLED with prejudice."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if logger.handlers:
        logger.handlers.clear()
    
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # NO StreamHandler allowed here. Only logs to file or custom TUI handler.
    
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        # Rotate logs: max size 5MB, keep 10 backups
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=5 * 1024 * 1024, 
            backupCount=10
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    if extra_handlers:
        for handler in extra_handlers:
            handler.setFormatter(formatter)
            logger.addHandler(handler)
    
    return logger
