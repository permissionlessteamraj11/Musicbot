import logging
import os
from logging.handlers import RotatingFileHandler

os.makedirs("logs", exist_ok=True)

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[
        RotatingFileHandler(
            "logs/musicbot.log",
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        ),
        logging.StreamHandler(),
    ],
)

# Suppress noisy libraries
for lib in ("pyrogram", "pytgcalls", "urllib3", "asyncio"):
    logging.getLogger(lib).setLevel(logging.WARNING)

LOGGER = logging.getLogger("MusicBot")
