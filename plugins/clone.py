import time
import asyncio
from pyrogram import Client, filters
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from bot import bot, START_TIME
from config import Config
from utils.database import get_stats, register_clone, get_all_clones, update_clone_heartbeat
from utils.decorators import owner_only
from utils.formatters import uptime_string, time_ago


ENV_TEMPLATE = """# ═══════════════════════════════════════════
# 🎵 MusicBot Configuration
# ═══════════════════════════════════════════

# ── Telegram ─────────────────────────────
API_ID=YOUR_API_ID
API_HASH=YOUR_API_HASH
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
STRING_SESSION=YOUR_PYROGRAM_STRING_SESSION
OWNER_ID=YOUR_TELEGRAM_USER_ID
SUDO_USERS=
LOG_GROUP_ID=

# ── Database ─────────────────────────────
MONGO_URI=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379

# ── Music APIs ────────────────────────────
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
GENIUS_API_TOKEN=
ACRCLOUD_HOST=
ACRCLOUD_KEY=
ACRCLOUD_SECRET=

# ── Bot Settings ──────────────────────────
BOT_NAME=🎵 My Music Bot
START_IMG_URL=
SUPPORT_LINK=https://t.me/yoursupport
UPSTREAM_REPO=https://github.com/yourrepo/musicbot
MAX_QUEUE_SIZE=100
AUTO_LEAVE_TIME=300

# ── Clone Settings ────────────────────────
CLONE_OWNER_BOT=
"""

VPS_DEPLOY_GUIDE = """🖥 **VPS Deployment Guide**

**Step 1 — Install dependencies:**
```bash
apt update && apt install -y ffmpeg python3.11 \\
  python3-pip python3-venv redis-server mongodb git curl
npm i -g pm2
```

**Step 2 — Clone & setup:**
```bash
git clone {repo}
cd musicbot
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

**Step 3 — Configure:**
```bash
cp .env.example .env
nano .env
```

**Step 4 — Generate String Session:**
```bash
python3 -c "from pyrogram import Client; \\
Client('s', api_id=API_ID, api_hash='API_HASH').run()"
```

**Step 5 — Start with PM2:**
```bash
pm2 start "python3 -m musicbot" --name MusicBot
pm2 save && pm2 startup
```

**Step 6 — Auto-update script:**
```bash
chmod +x update.sh
./update.sh  # to update anytime
```

✅ Bot is now running! Check `/stats` to verify.
"""

HEROKU_DEPLOY_GUIDE = """☁️ **Heroku Deployment Guide**

**Step 1** — Click the Deploy button below\n
**Step 2** — Fill in the config vars (env variables)\n
**Step 3** — Set `BOT_TOKEN`, `API_ID`, `API_HASH`, `OWNER_ID`, `MONGO_URI`, `STRING_SESSION`\n
**Step 4** — Deploy and scale the worker dyno:
```
heroku ps:scale worker=1
```

⚠️ **Note:** Heroku free tier may not support PyTgCalls well.
Recommended: Railway, Render, or a proper VPS.
"""


@bot.on_message(filters.command(["clone"]) & filters.private)
@owner_only
async def clone_cmd(client: Client, message: Message):
    me = await client.get_me()
    text = (
        f"🤖 **Clone {Config.BOT_NAME}**\n\n"
        f"Create your own music bot! Follow the steps below.\n\n"
        f"**What you need:**\n"
        f"├ API ID & Hash → [my.telegram.org](https://my.telegram.org)\n"
        f"├ Bot Token → [@BotFather](https://t.me/BotFather)\n"
        f"├ String Session → Generate using the session script\n"
        f"├ MongoDB URI → [MongoDB Atlas](https://cloud.mongodb.com) (free)\n"
        f"└ VPS → Any Ubuntu 22.04 server (1GB RAM min)\n\n"
        f"📁 **Source Code:** `{Config.UPSTREAM_REPO}`"
    )
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📦 VPS Guide", callback_data="clone_vps"),
            InlineKeyboardButton("☁️ Heroku Guide", callback_data="clone_heroku"),
        ],
        [
            InlineKeyboardButton("📋 .env Template", callback_data="clone_env"),
            InlineKeyboardButton("⚙️ Config Options", callback_data="clone_config"),
        ],
        [
            InlineKeyboardButton(
                "🔗 Source Code",
                url=Config.UPSTREAM_REPO,
            )
        ],
    ])
    await message.reply_text(text, reply_markup=buttons)


@bot.on_callback_query(filters.regex(r"^clone_(vps|heroku|env|config)$"))
async def clone_callback(client: Client, query: CallbackQuery):
    action = query.matches[0].group(1)

    if action == "vps":
        await query.message.edit_text(
            VPS_DEPLOY_GUIDE.format(repo=Config.UPSTREAM_REPO),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("« Back", callback_data="clone_back")]
            ]),
        )
    elif action == "heroku":
        await query.message.edit_text(
            HEROKU_DEPLOY_GUIDE,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("« Back", callback_data="clone_back")]
            ]),
        )
    elif action == "env":
        # Send .env template as file
        await query.answer()
        import io
        file = io.BytesIO(ENV_TEMPLATE.encode())
        file.name = ".env.example"
        await query.message.reply_document(
            file,
            caption="📋 Fill in all values and rename to `.env`",
        )
        return
    elif action == "config":
        text = (
            "⚙️ **Customizable Config Options:**\n\n"
            "`BOT_NAME` — Your bot's display name\n"
            "`START_IMG_URL` — Custom start image URL\n"
            "`SUPPORT_LINK` — Your support group link\n"
            "`MAX_QUEUE_SIZE` — Max songs in queue (default 100)\n"
            "`AUTO_LEAVE_TIME` — Seconds before auto-leave (default 300)\n"
            "`VOTE_SKIP_NEEDED` — Votes needed to skip (default 3)\n\n"
            "Set these in your `.env` file."
        )
        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("« Back", callback_data="clone_back")]
            ]),
        )
    await query.answer()


@bot.on_callback_query(filters.regex(r"^clone_back$"))
async def clone_back_callback(client: Client, query: CallbackQuery):
    me = await client.get_me()
    text = (
        f"🤖 **Clone {Config.BOT_NAME}**\n\n"
        f"Create your own music bot!\n\n"
        f"📁 **Source:** `{Config.UPSTREAM_REPO}`"
    )
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📦 VPS Guide", callback_data="clone_vps"),
            InlineKeyboardButton("☁️ Heroku Guide", callback_data="clone_heroku"),
        ],
        [
            InlineKeyboardButton("📋 .env Template", callback_data="clone_env"),
            InlineKeyboardButton("⚙️ Config Options", callback_data="clone_config"),
        ],
        [InlineKeyboardButton("🔗 Source Code", url=Config.UPSTREAM_REPO)],
    ])
    await query.message.edit_text(text, reply_markup=buttons)
    await query.answer()


@bot.on_message(filters.command(["clones"]) & filters.private)
@owner_only
async def clones_list_cmd(client: Client, message: Message):
    clones = await get_all_clones()
    if not clones:
        await message.reply_text("📭 No registered clones yet.")
        return
    text = f"🤖 **Registered Clones ({len(clones)}):**\n\n"
    now = time.time()
    for c in clones:
        last = c.get("last_heartbeat", 0)
        ago = time_ago(last)
        status = "🟢" if (now - last) < 600 else "🔴"
        token_short = c.get("bot_token", "???")[:10] + "..."
        text += (
            f"{status} `{token_short}`\n"
            f"  👥 Groups: {c.get('groups_count', 0)}\n"
            f"  🕐 Last seen: {ago}\n\n"
        )
    await message.reply_text(text)


@bot.on_message(filters.command(["cloneconfig"]) & filters.private)
@owner_only
async def cloneconfig_cmd(client: Client, message: Message):
    text = (
        "⚙️ **Clone Configuration**\n\n"
        f"Bot Name: `{Config.BOT_NAME}`\n"
        f"Support: `{Config.SUPPORT_LINK}`\n"
        f"Upstream: `{Config.UPSTREAM_REPO}`\n"
        f"Max Queue: `{Config.MAX_QUEUE_SIZE}`\n"
        f"Auto Leave: `{Config.AUTO_LEAVE_TIME}s`\n"
        f"Vote Skip: `{Config.VOTE_SKIP_NEEDED} votes`\n\n"
        "Edit these in your `.env` file and restart."
    )
    await message.reply_text(text)


# ── Heartbeat task (run on startup) ──────────────────────────────────────────

async def start_heartbeat():
    """Send heartbeat to owner bot every 5 minutes."""
    if not Config.CLONE_OWNER_BOT:
        return
    from assistant import get_active_chats
    while True:
        try:
            groups_count = len(get_active_chats())
            await update_clone_heartbeat(Config.BOT_TOKEN, groups_count)
        except Exception:
            pass
        await asyncio.sleep(300)
