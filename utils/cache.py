import json
import aioredis
from config import Config
from utils.logger import LOGGER

_redis = None


async def get_redis():
    global _redis
    if _redis is None:
        _redis = await aioredis.from_url(
            Config.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
        LOGGER.info("Redis connected.")
    return _redis


# ── Audio URL Cache ───────────────────────────────────────────────────────────

async def cache_audio_url(key: str, data: dict, ttl: int = Config.CACHE_TTL):
    r = await get_redis()
    await r.setex(f"audio:{key}", ttl, json.dumps(data))


async def get_cached_audio(key: str) -> dict | None:
    r = await get_redis()
    val = await r.get(f"audio:{key}")
    return json.loads(val) if val else None


# ── Rate Limiter ──────────────────────────────────────────────────────────────

async def check_rate_limit(user_id: int, limit: int = 3, window: int = 60) -> bool:
    """Returns True if under limit, False if rate-limited."""
    r = await get_redis()
    key = f"rate:{user_id}"
    count = await r.get(key)
    if count is None:
        await r.setex(key, window, 1)
        return True
    count = int(count)
    if count >= limit:
        return False
    await r.incr(key)
    return True


# ── Vote Skip ─────────────────────────────────────────────────────────────────

async def add_vote_skip(chat_id: int, user_id: int) -> int:
    r = await get_redis()
    key = f"voteskip:{chat_id}"
    await r.sadd(key, user_id)
    await r.expire(key, 120)
    return await r.scard(key)


async def clear_vote_skip(chat_id: int):
    r = await get_redis()
    await r.delete(f"voteskip:{chat_id}")


async def get_vote_count(chat_id: int) -> int:
    r = await get_redis()
    return await r.scard(f"voteskip:{chat_id}")


# ── Anti-Abuse Blacklist ──────────────────────────────────────────────────────

async def abuse_ban(user_id: int, duration: int = 3600):
    r = await get_redis()
    await r.setex(f"abuseban:{user_id}", duration, 1)


async def is_abuse_banned(user_id: int) -> bool:
    r = await get_redis()
    return bool(await r.get(f"abuseban:{user_id}"))


# ── Sleep Timer ───────────────────────────────────────────────────────────────

async def set_sleep_timer(chat_id: int, seconds: int):
    r = await get_redis()
    await r.setex(f"sleep:{chat_id}", seconds, 1)


async def check_sleep_timer(chat_id: int) -> bool:
    r = await get_redis()
    return not bool(await r.get(f"sleep:{chat_id}"))


async def clear_sleep_timer(chat_id: int):
    r = await get_redis()
    await r.delete(f"sleep:{chat_id}")


# ── Generic KV ───────────────────────────────────────────────────────────────

async def set_key(key: str, value, ttl: int = None):
    r = await get_redis()
    val = json.dumps(value)
    if ttl:
        await r.setex(key, ttl, val)
    else:
        await r.set(key, val)


async def get_key(key: str):
    r = await get_redis()
    val = await r.get(key)
    return json.loads(val) if val else None


async def del_key(key: str):
    r = await get_redis()
    await r.delete(key)
