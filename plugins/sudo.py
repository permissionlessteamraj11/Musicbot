import asyncio
import os
import time
import psutil
from pyrogram import Client, filters
from pyrogram.types import Message
from bot import bot, START_TIME
from config import Config
from utils.database import (
    add_sudo, del_sudo, get_sudo_users, ban_user, unban_user,
    get_stats, get_all_chat_ids
)
from utils.decorators import owner_only, sudo_only
from utils.formatters import uptime_string
from utils.cache import set_key, get_key
from assistant import get_active_chats, is_active
from strings import get_string


@bot.on_message(filters.command(["addsudo"]) & filters.private)
@owner_only
async def addsudo_cmd(client: Client, message: Message):
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
        await message.reply_text("❌ Reply to user or mention them.")
        return
    await add_sudo(target.id)
    await message.reply_text(f"✅ [{target.first_name}](tg://user?id={target.id}) added to sudo.")


@bot.on_message(filters.command(["delsudo"]) & filters.private)
@owner_only
async def delsudo_cmd(client: Client, message: Message):
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
        await message.reply_text("❌ Reply to user or mention them.")
        return
    await del_sudo(target.id)
    await message.reply_text(f"✅ [{target.first_name}](tg://user?id={target.id}) removed from sudo.")


@bot.on_message(filters.command(["sudolist"]) & filters.private)
@owner_only
async def sudolist_cmd(client: Client, message: Message):
    sudos = await get_sudo_users()
    if not sudos:
        await message.reply_text("📭 No sudo users.")
        return
    text = "🛡 **Sudo Users:**\n\n"
    for uid in sudos:
        try:
            u = await client.get_users(uid)
            text += f"• [{u.first_name}](tg://user?id={uid}) (`{uid}`)\n"
        except Exception:
            text += f"• `{uid}`\n"
    await message.reply_text(text)


@bot.on_message(filters.command(["gban"]))
@sudo_only
async def gban_cmd(client: Client, message: Message):
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
        await message.reply_text("❌ Specify a user.")
        return
    if target.id == Config.OWNER_ID:
        await message.reply_text("❌ Cannot ban the owner.")
        return
    await ban_user(target.id)
    await message.reply_text(f"🚫 [{target.first_name}](tg://user?id={target.id}) globally banned.")


@bot.on_message(filters.command(["ungban"]))
@sudo_only
async def ungban_cmd(client: Client, message: Message):
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
        await message.reply_text("❌ Specify a user.")
        return
    await unban_user(target.id)
    await message.reply_text(f"✅ [{target.first_name}](tg://user?id={target.id}) unbanned.")


@bot.on_message(filters.command(["broadcast"]) & filters.private)
@owner_only
async def broadcast_cmd(client: Client, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        await message.reply_text("❌ Usage: `/broadcast <text>` or reply to a message.")
        return
    broadcast_text = (
        " ".join(message.command[1:])
        if len(message.command) > 1
        else message.reply_to_message.text
    )
    chats = await get_all_chat_ids()
    status = await message.reply_text(f"📢 Broadcasting to {len(chats)} groups...")
    success = fail = 0
    for chat_id in chats:
        try:
            await client.send_message(chat_id, broadcast_text)
            success += 1
            await asyncio.sleep(0.1)
        except Exception:
            fail += 1
    await status.edit_text(
        f"✅ Broadcast complete!\n\n✅ Success: {success}\n❌ Failed: {fail}"
    )


@bot.on_message(filters.command(["stats"]))
@sudo_only
async def stats_cmd(client: Client, message: Message):
    data = await get_stats()
    active_vc = len(get_active_chats())
    uptime = uptime_string(START_TIME)

    # System stats
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    text = (
        f"📊 **Bot Statistics**\n\n"
        f"├ 👥 Groups: `{data['groups']}`\n"
        f"├ 👤 Users: `{data['users']}`\n"
        f"├ 🎵 Total Plays: `{data['plays']}`\n"
        f"├ 🔊 Active VCs: `{active_vc}`\n"
        f"└ ⏱ Uptime: `{uptime}`\n\n"
        f"🖥 **System**\n"
        f"├ CPU: `{cpu}%`\n"
        f"├ RAM: `{mem.percent}%` ({mem.used // 1024 // 1024}MB / {mem.total // 1024 // 1024}MB)\n"
        f"└ Disk: `{disk.percent}%` ({disk.used // 1024 // 1024 // 1024}GB / {disk.total // 1024 // 1024 // 1024}GB)"
    )
    await message.reply_text(text)


@bot.on_message(filters.command(["logs"]) & filters.private)
@owner_only
async def logs_cmd(client: Client, message: Message):
    log_path = "logs/musicbot.log"
    if os.path.exists(log_path):
        await client.send_document(message.chat.id, log_path, caption="📋 Bot Logs")
    else:
        await message.reply_text("❌ Log file not found.")


@bot.on_message(filters.command(["restart"]) & filters.private)
@owner_only
async def restart_cmd(client: Client, message: Message):
    await message.reply_text("🔄 Restarting bot...")
    await set_key("restart_chat", message.chat.id)
    await set_key("restart_msg", message.id)
    os.execv("/proc/self/exe", ["python"] + ["-m", "musicbot"])


@bot.on_message(filters.command(["update"]) & filters.private)
@owner_only
async def update_cmd(client: Client, message: Message):
    status = await message.reply_text("⬇️ Pulling latest changes from Git...")
    proc = await asyncio.create_subprocess_shell(
        "git pull origin main",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    out = stdout.decode() + stderr.decode()
    await status.edit_text(f"```\n{out[:3000]}\n```\n\n🔄 Restarting...")
    await asyncio.sleep(2)
    os.execv("/proc/self/exe", ["python"] + ["-m", "musicbot"])


@bot.on_message(filters.command(["maintenance"]) & filters.private)
@owner_only
async def maintenance_cmd(client: Client, message: Message):
    if len(message.command) < 2 or message.command[1] not in ("on", "off"):
        await message.reply_text("❌ Usage: `/maintenance on|off`")
        return
    mode = message.command[1] == "on"
    await set_key("maintenance_mode", mode)
    status = "🔧 **Maintenance mode ON**\nAll non-owner commands disabled." if mode else "✅ **Maintenance mode OFF**"
    await message.reply_text(status)


@bot.on_message(filters.command(["activevc"]))
@sudo_only
async def activevc_cmd(client: Client, message: Message):
    chats = get_active_chats()
    if not chats:
        await message.reply_text("ℹ️ No active voice chats right now.")
        return
    text = f"🔊 **Active Voice Chats ({len(chats)}):**\n\n"
    for cid in chats:
        try:
            chat = await client.get_chat(cid)
            text += f"• [{chat.title}](tg://openmessage?chat_id={cid}) (`{cid}`)\n"
        except Exception:
            text += f"• `{cid}`\n"
    await message.reply_text(text)


@bot.on_message(filters.command(["ping"]))
async def ping_cmd(client: Client, message: Message):
    start = time.time()
    msg = await message.reply_text("🏓 Pinging...")
    ms = round((time.time() - start) * 1000)
    await msg.edit_text(f"🏓 **Pong!**\n⚡ Speed: `{ms}ms`")
