import os
import logging
from logging.handlers import RotatingFileHandler

import config

LOG_DIR = os.path.dirname(config.LOG_FILE)
if not os.path.exists(LOG_DIR):
    try:
        os.makedirs(LOG_DIR)
    except OSError:
        pass

fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

_logger = logging.getLogger("tourist_guide")
_logger.setLevel(getattr(logging, config.LOG_LEVEL.upper(), logging.INFO))
_handler = RotatingFileHandler(config.LOG_FILE, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
_handler.setFormatter(fmt)
_logger.addHandler(_handler)
_console = logging.StreamHandler()
_console.setFormatter(fmt)
_logger.addHandler(_console)

AUDIT_FILE = os.path.join(LOG_DIR, "audit.log")
_audit = logging.getLogger("tourist_guide_audit")
_audit.setLevel(logging.INFO)
_audit_handler = RotatingFileHandler(AUDIT_FILE, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
_audit_handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
_audit.addHandler(_audit_handler)

def get_logger():
    return _logger

def get_audit():
    return _audit
