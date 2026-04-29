from functools import wraps
from pyrogram import Client
from pyrogram.types import Message
from config import Config
from utils.database import get_auth_users, get_group, is_banned, get_sudo_users
from utils.cache import is_abuse_banned, check_rate_limit
from strings import get_string


def _is_sudo(user_id: int) -> bool:
    return user_id == Config.OWNER_ID or user_id in Config.SUDO_USERS


def owner_only(func):
    @wraps(func)
    async def wrapper(client: Client, message: Message):
        if message.from_user.id != Config.OWNER_ID:
            await message.reply_text("❌ Only bot owner can use this command.")
            return
        return await func(client, message)
    return wrapper


def sudo_only(func):
    @wraps(func)
    async def wrapper(client: Client, message: Message):
        uid = message.from_user.id
        sudo_list = await get_sudo_users()
        if uid != Config.OWNER_ID and uid not in sudo_list:
            await message.reply_text("❌ Only sudo users can use this command.")
            return
        return await func(client, message)
    return wrapper


def admin_or_auth(func):
    @wraps(func)
    async def wrapper(client: Client, message: Message):
        uid = message.from_user.id
        cid = message.chat.id

        # Check global ban
        if await is_banned(uid):
            await message.reply_text("🚫 You are globally banned from using this bot.")
            return

        # Check abuse ban
        if await is_abuse_banned(uid):
            await message.reply_text("⏳ You are temporarily blocked due to spam. Try again later.")
            return

        # Owner/sudo bypass
        if _is_sudo(uid):
            return await func(client, message)

        # Check if admin
        try:
            member = await client.get_chat_member(cid, uid)
            if member.status in ("administrator", "creator"):
                return await func(client, message)
        except Exception:
            pass

        # Check auth users
        auth_users = await get_auth_users(cid)
        if uid in auth_users:
            return await func(client, message)

        # Check lock
        group = await get_group(cid)
        if group.get("lock"):
            await message.reply_text("🔒 Bot is locked. Only admins can use commands.")
            return

        return await func(client, message)
    return wrapper


def admin_only(func):
    @wraps(func)
    async def wrapper(client: Client, message: Message):
        uid = message.from_user.id
        cid = message.chat.id

        if _is_sudo(uid):
            return await func(client, message)

        try:
            member = await client.get_chat_member(cid, uid)
            if member.status in ("administrator", "creator"):
                return await func(client, message)
        except Exception:
            pass

        await message.reply_text("❌ Only group admins can use this command.")
    return wrapper


def rate_limited(func):
    @wraps(func)
    async def wrapper(client: Client, message: Message):
        uid = message.from_user.id
        if _is_sudo(uid):
            return await func(client, message)

        allowed = await check_rate_limit(uid, Config.PLAY_RATE_LIMIT)
        if not allowed:
            await message.reply_text(
                f"⚠️ Rate limit exceeded! Max {Config.PLAY_RATE_LIMIT} plays per minute."
            )
            return
        return await func(client, message)
    return wrapper


def maintenance_check(func):
    @wraps(func)
    async def wrapper(client: Client, message: Message):
        from utils.cache import get_key
        maintenance = await get_key("maintenance_mode")
        if maintenance and message.from_user.id != Config.OWNER_ID:
            await message.reply_text("🔧 Bot is under maintenance. Please try again later.")
            return
        return await func(client, message)
    return wrapper
