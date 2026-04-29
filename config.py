import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ── Telegram ──────────────────────────────────────────
    API_ID: int = int(os.getenv("API_ID", 0))
    API_HASH: str = os.getenv("API_HASH", "")
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    STRING_SESSIONS: list = [
        s.strip()
        for s in os.getenv("STRING_SESSION", "").split(",")
        if s.strip()
    ]
    OWNER_ID: int = int(os.getenv("OWNER_ID", 0))
    SUDO_USERS: list = [
        int(x) for x in os.getenv("SUDO_USERS", "").split(",") if x.strip().isdigit()
    ]
    LOG_GROUP_ID: int = int(os.getenv("LOG_GROUP_ID", 0))

    # ── Database ──────────────────────────────────────────
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # ── Music APIs ────────────────────────────────────────
    SPOTIFY_CLIENT_ID: str = os.getenv("SPOTIFY_CLIENT_ID", "")
    SPOTIFY_CLIENT_SECRET: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    GENIUS_API_TOKEN: str = os.getenv("GENIUS_API_TOKEN", "")
    ACRCLOUD_HOST: str = os.getenv("ACRCLOUD_HOST", "")
    ACRCLOUD_KEY: str = os.getenv("ACRCLOUD_KEY", "")
    ACRCLOUD_SECRET: str = os.getenv("ACRCLOUD_SECRET", "")

    # ── Bot Settings ──────────────────────────────────────
    BOT_NAME: str = os.getenv("BOT_NAME", "🎵 Music Bot")
    START_IMG_URL: str = os.getenv("START_IMG_URL", "")
    SUPPORT_LINK: str = os.getenv("SUPPORT_LINK", "https://t.me/support")
    UPSTREAM_REPO: str = os.getenv("UPSTREAM_REPO", "https://github.com/yourrepo/musicbot")
    MAX_QUEUE_SIZE: int = int(os.getenv("MAX_QUEUE_SIZE", 100))
    AUTO_LEAVE_TIME: int = int(os.getenv("AUTO_LEAVE_TIME", 300))

    # ── Clone Settings ────────────────────────────────────
    CLONE_OWNER_BOT: str = os.getenv("CLONE_OWNER_BOT", "")

    # ── Audio Quality ─────────────────────────────────────
    AUDIO_BITRATE: int = 320          # kbps
    AUDIO_SAMPLE_RATE: int = 48000    # Hz
    AUDIO_CHANNELS: int = 2           # stereo

    # ── Redis Cache TTL ───────────────────────────────────
    CACHE_TTL: int = 7200             # 2 hours

    # ── Limits ────────────────────────────────────────────
    MAX_DURATION: int = 18000         # 5 hours in seconds
    VOTE_SKIP_NEEDED: int = 3
    PLAY_RATE_LIMIT: int = 3          # plays per minute per user
