from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
from utils.logger import LOGGER
import time

_client = None
_db = None


async def get_db():
    global _client, _db
    if _db is None:
        _client = AsyncIOMotorClient(Config.MONGO_URI)
        _db = _client["musicbot"]
        LOGGER.info("MongoDB connected.")
    return _db


# ── Groups ────────────────────────────────────────────────────────────────────

async def get_group(chat_id: int) -> dict:
    db = await get_db()
    doc = await db.groups.find_one({"chat_id": chat_id})
    if not doc:
        doc = {
            "chat_id": chat_id,
            "settings": {},
            "auth_users": [],
            "blacklist": [],
            "prefix": "/",
            "lock": False,
            "log_channel": None,
            "lang": "en",
            "quality": "ultra",
            "247_mode": False,
            "queue_limit": 10,
        }
        await db.groups.insert_one(doc)
    return doc


async def update_group(chat_id: int, data: dict):
    db = await get_db()
    await db.groups.update_one(
        {"chat_id": chat_id}, {"$set": data}, upsert=True
    )


async def auth_user(chat_id: int, user_id: int):
    db = await get_db()
    await db.groups.update_one(
        {"chat_id": chat_id}, {"$addToSet": {"auth_users": user_id}}, upsert=True
    )


async def unauth_user(chat_id: int, user_id: int):
    db = await get_db()
    await db.groups.update_one(
        {"chat_id": chat_id}, {"$pull": {"auth_users": user_id}}
    )


async def get_auth_users(chat_id: int) -> list:
    doc = await get_group(chat_id)
    return doc.get("auth_users", [])


async def blacklist_song(chat_id: int, song: str):
    db = await get_db()
    await db.groups.update_one(
        {"chat_id": chat_id}, {"$addToSet": {"blacklist": song.lower()}}, upsert=True
    )


async def get_blacklist(chat_id: int) -> list:
    doc = await get_group(chat_id)
    return doc.get("blacklist", [])


# ── Users ─────────────────────────────────────────────────────────────────────

async def get_user(user_id: int) -> dict:
    db = await get_db()
    doc = await db.users.find_one({"user_id": user_id})
    if not doc:
        doc = {"user_id": user_id, "total_plays": 0, "banned": False}
        await db.users.insert_one(doc)
    return doc


async def increment_plays(user_id: int):
    db = await get_db()
    await db.users.update_one(
        {"user_id": user_id}, {"$inc": {"total_plays": 1}}, upsert=True
    )


async def ban_user(user_id: int):
    db = await get_db()
    await db.users.update_one(
        {"user_id": user_id}, {"$set": {"banned": True}}, upsert=True
    )


async def unban_user(user_id: int):
    db = await get_db()
    await db.users.update_one(
        {"user_id": user_id}, {"$set": {"banned": False}}, upsert=True
    )


async def is_banned(user_id: int) -> bool:
    doc = await get_user(user_id)
    return doc.get("banned", False)


# ── Queue Backup ──────────────────────────────────────────────────────────────

async def save_queue(chat_id: int, queue: list, pos: int):
    db = await get_db()
    await db.queue_backup.update_one(
        {"chat_id": chat_id},
        {"$set": {"queue_array": queue, "current_pos": pos}},
        upsert=True,
    )


async def load_queue(chat_id: int) -> dict:
    db = await get_db()
    return await db.queue_backup.find_one({"chat_id": chat_id}) or {}


async def clear_queue_backup(chat_id: int):
    db = await get_db()
    await db.queue_backup.delete_one({"chat_id": chat_id})


# ── Plays Log ─────────────────────────────────────────────────────────────────

async def log_play(chat_id: int, user_id: int, song: str):
    db = await get_db()
    await db.plays_log.insert_one(
        {"chat_id": chat_id, "user_id": user_id, "song": song, "timestamp": time.time()}
    )


async def get_top_songs(chat_id: int, limit: int = 10) -> list:
    db = await get_db()
    pipeline = [
        {"$match": {"chat_id": chat_id}},
        {"$group": {"_id": "$song", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
    ]
    return await db.plays_log.aggregate(pipeline).to_list(limit)


async def get_top_requesters(chat_id: int, limit: int = 10) -> list:
    db = await get_db()
    pipeline = [
        {"$match": {"chat_id": chat_id}},
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
    ]
    return await db.plays_log.aggregate(pipeline).to_list(limit)


async def get_recent_plays(chat_id: int, limit: int = 10) -> list:
    db = await get_db()
    cursor = db.plays_log.find({"chat_id": chat_id}).sort("timestamp", -1).limit(limit)
    return await cursor.to_list(limit)


# ── Sudo Users ────────────────────────────────────────────────────────────────

async def add_sudo(user_id: int):
    db = await get_db()
    await db.sudo_users.update_one(
        {"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True
    )


async def del_sudo(user_id: int):
    db = await get_db()
    await db.sudo_users.delete_one({"user_id": user_id})


async def get_sudo_users() -> list:
    db = await get_db()
    cursor = db.sudo_users.find({})
    docs = await cursor.to_list(None)
    return [d["user_id"] for d in docs]


# ── Clone Tracking ────────────────────────────────────────────────────────────

async def register_clone(bot_token: str, owner_id: int, config: dict):
    db = await get_db()
    await db.clones.update_one(
        {"bot_token": bot_token},
        {
            "$set": {
                "owner_id": owner_id,
                "config": config,
                "last_heartbeat": time.time(),
                "groups_count": 0,
            }
        },
        upsert=True,
    )


async def update_clone_heartbeat(bot_token: str, groups_count: int = 0):
    db = await get_db()
    await db.clones.update_one(
        {"bot_token": bot_token},
        {"$set": {"last_heartbeat": time.time(), "groups_count": groups_count}},
    )


async def get_all_clones() -> list:
    db = await get_db()
    return await db.clones.find({}).to_list(None)


# ── Stats ─────────────────────────────────────────────────────────────────────

async def get_stats() -> dict:
    db = await get_db()
    total_groups = await db.groups.count_documents({})
    total_users = await db.users.count_documents({})
    total_plays = await db.plays_log.count_documents({})
    return {
        "groups": total_groups,
        "users": total_users,
        "plays": total_plays,
    }


async def get_all_chat_ids() -> list:
    db = await get_db()
    cursor = db.groups.find({}, {"chat_id": 1})
    docs = await cursor.to_list(None)
    return [d["chat_id"] for d in docs]
