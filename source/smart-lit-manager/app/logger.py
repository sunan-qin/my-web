"""
Logging and error-handling utilities for Smart Literature Manager.
Provides structured logging, a global exception hook, and safe wrappers.
"""
import logging
import os
import sys
import traceback
from datetime import datetime
from typing import Callable, Optional

def _get_data_dir():
    primary = os.path.join(os.path.expanduser("~"), ".smart-lit-manager")
    try:
        os.makedirs(primary, exist_ok=True)
        testf = os.path.join(primary, ".wtest")
        with open(testf, "w"): pass
        os.remove(testf)
        return primary
    except (OSError, PermissionError):
        fb = os.path.join(os.environ.get("TEMP", "/tmp"), "smart-lit-manager")
        os.makedirs(fb, exist_ok=True)
        return fb

LOG_DIR = _get_data_dir()
LOG_FILE = os.path.join(LOG_DIR, "app.log")


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure the application-wide logger."""
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger("SmartLitManager")
    logger.setLevel(level)

    # Avoid adding duplicate handlers on re-import
    if not logger.handlers:
        fh = logging.FileHandler(LOG_FILE, encoding="utf-8", mode="a")
        fh.setLevel(level)
        fh.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        logger.addHandler(fh)

        # Also log to stderr during development
        sh = logging.StreamHandler(sys.stderr)
        sh.setLevel(logging.WARNING)
        sh.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        logger.addHandler(sh)

    return logger


# Module-level convenience
logger = setup_logging()


class ErrorHandler:
    """Wraps risky operations with logging and user-facing error messages."""

    @staticmethod
    def safe_call(fn, on_error=None, default=None):
        """Execute fn with no args. On exception, log and return default."""
        try:
            return fn()
        except Exception as exc:
            logger.error("%s | %s", on_error or fn.__name__, exc, exc_info=True)
            return default

    @staticmethod
    def safe_call_with_args(fn, args, kwargs=None, on_error=None, default=None):
        """Like safe_call but passes args and kwargs to fn."""
        try:
            return fn(*args, **(kwargs or {}))
        except Exception as exc:
            logger.error("%s | %s", on_error or fn.__name__, exc, exc_info=True)
            return default


def install_global_exception_hook():
    """Install a top-level hook that logs all unhandled exceptions."""
    def hook(exc_type, exc_value, exc_tb):
        msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        logger.critical("Unhandled exception:\n%s", msg)
        print(msg, file=sys.stderr)

    sys.excepthook = hook


def friendly_error(message: str) -> str:
    """Return a human-readable error message with a timestamp."""
    ts = datetime.now().strftime("%H:%M:%S")
    return f"[{ts}] Error: {message}"
