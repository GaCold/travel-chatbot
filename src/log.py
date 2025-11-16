import logging
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
level = getattr(logging, LOG_LEVEL, logging.INFO)

# Logging setup
logging.basicConfig(level=level)
logger = logging.getLogger(__name__)