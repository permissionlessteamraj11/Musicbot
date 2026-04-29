import time
from pyrogram import Client
from config import Config
from utils.logger import LOGGER

START_TIME = time.time()

bot = Client(
    "MusicBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins=dict(root="plugins"),
)

LOGGER.info("Bot client initialized.")
