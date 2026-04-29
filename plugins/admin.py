from pyrogram import Client, filters
from pyrogram.types import Message
from bot import bot
from utils.database import (
    get_group, update_group, auth_user, unauth_user,
    get_auth_users, blacklist_song, get_blacklist
)
from utils.decorators import admin_only
from strings import get_string


async def _lang(cid):
    g = await get_group(cid); return g.get("lang", "en")


@bot.on_message(filters.command(["lock"]) & filters.group)
@admin_only
async def lock_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    lang = await _lang(chat_id)
    await update_group(chat_id, {"lock": True})
    await message.reply_text(get_string(lang, "locked_msg"))


@bot.on_message(filters.command(["unlock"]) & filters.group)
@admin_only
async def unlock_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    lang = await _lang(chat_id)
    await update_group(chat_id, {"lock": False})
    await message.reply_text(get_string(lang, "unlocked_msg"))


@bot.on_message(filters.command(["auth"]) & filters.group)
@admin_only
async def auth_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    lang = await _lang(chat_id)
    target = None
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            target = await client.get_users(message.command[1].lstrip("@"))
        except Exception:
            await message.reply_text("❌ User not found.")
            return
    if not target:
        await message.reply_text("❌ Reply to a user or mention them.")
        return
    await auth_user(chat_id, target.id)
    await message.reply_text(
        get_string(lang, "authed", user=f"[{target.first_name}](tg://user?id={target.id})")
    )


@bot.on_message(filters.command(["unauth"]) & filters.group)
@admin_only
async def unauth_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    lang = await _lang(chat_id)
    target = None
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            target = await client.get_users(message.command[1].lstrip("@"))
        except Exception:
            await message.reply_text("❌ User not found.")
            return
    if not target:
        await message.reply_text("❌ Reply to a user or mention them.")
        return
    await unauth_user(chat_id, target.id)
    await message.reply_text(
        get_string(lang, "unauthed", user=f"[{target.first_name}](tg://user?id={target.id})")
    )


@bot.on_message(filters.command(["authusers"]) & filters.group)
@admin_only
async def authusers_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    users = await get_auth_users(chat_id)
    if not users:
        await message.reply_text("📭 No authorized users.")
        return
    text = "✅ **Authorized Users:**\n\n"
    for uid in users:
        try:
            u = await client.get_users(uid)
            text += f"• [{u.first_name}](tg://user?id={uid}) (`{uid}`)\n"
        except Exception:
            text += f"• `{uid}`\n"
    await message.reply_text(text)


@bot.on_message(filters.command(["setlimit"]) & filters.group)
@admin_only
async def setlimit_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    lang = await _lang(chat_id)
    if len(message.command) < 2:
        await message.reply_text("❌ Usage: `/setlimit <number>`")
        return
    try:
        n = int(message.command[1])
        if n < 1 or n > 100:
            raise ValueError
    except ValueError:
        await message.reply_text("❌ Invalid. Use a number between 1 and 100.")
        return
    await update_group(chat_id, {"queue_limit": n})
    await message.reply_text(get_string(lang, "limit_set", n=n))


@bot.on_message(filters.command(["setlog"]) & filters.group)
@admin_only
async def setlog_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    lang = await _lang(chat_id)
    if len(message.command) < 2:
        await message.reply_text("❌ Usage: `/setlog <channel_id or @username>`")
        return
    ch = message.command[1]
    try:
        channel = await client.get_chat(ch)
        await update_group(chat_id, {"log_channel": channel.id})
        await message.reply_text(get_string(lang, "log_set", ch=channel.title))
    except Exception:
        await message.reply_text("❌ Channel not found. Make sure I'm an admin there.")


@bot.on_message(filters.command(["setprefix"]) & filters.group)
@admin_only
async def setprefix_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    lang = await _lang(chat_id)
    if len(message.command) < 2:
        await message.reply_text("❌ Usage: `/setprefix <!>`")
        return
    prefix = message.command[1][:3]
    await update_group(chat_id, {"prefix": prefix})
    await message.reply_text(get_string(lang, "prefix_set", prefix=prefix))


@bot.on_message(filters.command(["blacklist", "bl"]) & filters.group)
@admin_only
async def blacklist_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    lang = await _lang(chat_id)
    if len(message.command) < 2:
        bl = await get_blacklist(chat_id)
        if not bl:
            await message.reply_text("📭 No songs blacklisted.")
            return
        text = "🚫 **Blacklisted Songs:**\n\n" + "\n".join(f"• `{s}`" for s in bl)
        await message.reply_text(text)
        return
    song = " ".join(message.command[1:]).lower()
    await blacklist_song(chat_id, song)
    await message.reply_text(get_string(lang, "blacklisted_song") + f"\n`{song}`")


@bot.on_message(filters.command(["setlang"]) & filters.group)
@admin_only
async def setlang_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    LANGS = {"en": "🇬🇧 English", "hi": "🇮🇳 Hindi"}
    if len(message.command) < 2 or message.command[1] not in LANGS:
        await message.reply_text(
            f"❌ Usage: `/setlang en|hi`\n\nAvailable: {', '.join(LANGS)}"
        )
        return
    lang = message.command[1]
    await update_group(chat_id, {"lang": lang})
    await message.reply_text(f"✅ Language set to {LANGS[lang]}")


@bot.on_message(filters.command(["topreq"]) & filters.group)
async def topreq_cmd(client: Client, message: Message):
    from utils.database import get_top_requesters
    chat_id = message.chat.id
    data = await get_top_requesters(chat_id, 10)
    if not data:
        await message.reply_text("📭 No data yet.")
        return
    text = "👑 **Top Requesters:**\n\n"
    for i, item in enumerate(data, 1):
        try:
            u = await client.get_users(item["_id"])
            name = u.first_name
        except Exception:
            name = f"User {item['_id']}"
        text += f"`{i}.` **{name}** — {item['count']} plays\n"
    await message.reply_text(text)


@bot.on_message(filters.command(["topsongs"]) & filters.group)
async def topsongs_cmd(client: Client, message: Message):
    from utils.database import get_top_songs
    chat_id = message.chat.id
    data = await get_top_songs(chat_id, 10)
    if not data:
        await message.reply_text("📭 No data yet.")
        return
    text = "🎵 **Top Songs:**\n\n"
    for i, item in enumerate(data, 1):
        text += f"`{i}.` {item['_id'][:45]} — **{item['count']}x**\n"
    await message.reply_text(text)
