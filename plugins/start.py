import asyncio
import io
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent
)
from bot import bot, START_TIME
from config import Config
from utils.database import get_stats
from utils.formatters import uptime_string
from strings import get_string

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    PIL_OK = True
except ImportError:
    PIL_OK = False


async def _build_start_card(bot_name: str, stats: dict, uptime: str) -> bytes | None:
    if not PIL_OK:
        return None
    import os

    def _draw():
        W, H = 640, 320
        img = Image.new("RGBA", (W, H), (12, 12, 22, 255))
        draw = ImageDraw.Draw(img)

        # Gradient strips
        for i in range(H):
            alpha = int(180 * (1 - i / H))
            draw.line([(0, i), (W, i)], fill=(80, 40, 120, alpha))

        # Glow circles
        for (cx, cy, r, col) in [
            (80, 80, 100, (120, 60, 200, 30)),
            (560, 240, 80, (60, 100, 200, 25)),
        ]:
            for dr in range(r, 0, -10):
                a = col[3] - int(col[3] * (1 - dr / r))
                draw.ellipse([cx - dr, cy - dr, cx + dr, cy + dr],
                             fill=(*col[:3], max(0, a)))

        # Title
        FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")
        def _font(name, size):
            try:
                return ImageFont.truetype(os.path.join(FONT_DIR, name), size)
            except Exception:
                return ImageFont.load_default()

        draw.text((W // 2, 80), "🎵", font=_font("Poppins-Bold.ttf", 48), fill=(255,255,255), anchor="mm")
        draw.text((W // 2, 140), bot_name, font=_font("Poppins-Bold.ttf", 28), fill=(255, 255, 255), anchor="mm")
        draw.text((W // 2, 178), "Blazing Fast • 320kbps • Multi-Source", 
                  font=_font("Poppins-Regular.ttf", 14), fill=(180, 150, 220), anchor="mm")

        # Stats bar
        y = 220
        draw.rounded_rectangle([40, y, W - 40, y + 60], radius=12, fill=(30, 20, 50, 200))
        items = [
            ("👥", f"{stats['groups']}", "Groups"),
            ("🎵", f"{stats['plays']}", "Plays"),
            ("⏱", uptime, "Uptime"),
        ]
        for i, (icon, val, label) in enumerate(items):
            x = 100 + i * 180
            draw.text((x, y + 14), f"{icon} {val}", font=_font("Poppins-Bold.ttf", 13),
                      fill=(200, 180, 255), anchor="mm")
            draw.text((x, y + 38), label, font=_font("Poppins-Regular.ttf", 11),
                      fill=(140, 130, 180), anchor="mm")

        buf = io.BytesIO()
        img.convert("RGB").save(buf, "PNG")
        buf.seek(0)
        return buf.read()

    return await asyncio.get_event_loop().run_in_executor(None, _draw)


def _start_buttons(me) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "➕ Add to Group",
                url=f"https://t.me/{me.username}?startgroup=true",
            ),
            InlineKeyboardButton("📞 Support", url=Config.SUPPORT_LINK),
        ],
        [
            InlineKeyboardButton("📊 Stats", callback_data="start_stats"),
            InlineKeyboardButton("🎵 Commands", callback_data="start_help"),
        ],
        [
            InlineKeyboardButton("👤 Owner", url=f"tg://user?id={Config.OWNER_ID}"),
            InlineKeyboardButton("🔗 Source", url=Config.UPSTREAM_REPO),
        ],
    ])


@bot.on_message(filters.command(["start"]) & filters.private)
async def start_cmd(client: Client, message: Message):
    me = await client.get_me()
    stats = await get_stats()
    uptime = uptime_string(START_TIME)

    text = get_string("en", "start_text",
                      bot_name=Config.BOT_NAME,
                      groups=stats["groups"],
                      users=stats["users"],
                      plays=stats["plays"],
                      uptime=uptime)

    card = await _build_start_card(Config.BOT_NAME, stats, uptime)
    buttons = _start_buttons(me)

    if card:
        await message.reply_photo(card, caption=text, reply_markup=buttons)
    elif Config.START_IMG_URL:
        await message.reply_photo(Config.START_IMG_URL, caption=text, reply_markup=buttons)
    else:
        await message.reply_text(text, reply_markup=buttons)


@bot.on_message(filters.command(["start"]) & filters.group)
async def start_group_cmd(client: Client, message: Message):
    me = await client.get_me()
    await message.reply_text(
        f"👋 Hi! I'm **{Config.BOT_NAME}**\n"
        f"Use `/play <song>` to start playing music!\n"
        f"📋 `/help` for all commands.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🎵 Commands", callback_data="start_help")
        ]]),
    )


@bot.on_message(filters.command(["help", "h"]))
async def help_cmd(client: Client, message: Message):
    text = get_string("en", "help_text", bot_name=Config.BOT_NAME)
    await message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("➕ Add to Group",
                url=f"https://t.me/{(await client.get_me()).username}?startgroup=true")
        ]]),
    )


@bot.on_callback_query(filters.regex(r"^start_(stats|help|back)$"))
async def start_callback(client: Client, query):
    action = query.matches[0].group(1)
    me = await client.get_me()

    if action == "stats":
        stats = await get_stats()
        from assistant import get_active_chats
        uptime = uptime_string(START_TIME)
        text = get_string("en", "stats_text",
                          groups=stats["groups"],
                          users=stats["users"],
                          plays=stats["plays"],
                          active_vc=len(get_active_chats()),
                          uptime=uptime)
        await query.message.edit_caption(
            text,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Back", callback_data="start_back")
            ]]),
        )

    elif action == "help":
        text = get_string("en", "help_text", bot_name=Config.BOT_NAME)
        try:
            await query.message.edit_caption(
                text,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("« Back", callback_data="start_back")
                ]]),
            )
        except Exception:
            await query.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("« Back", callback_data="start_back")
                ]]),
            )

    elif action == "back":
        stats = await get_stats()
        uptime = uptime_string(START_TIME)
        text = get_string("en", "start_text",
                          bot_name=Config.BOT_NAME,
                          groups=stats["groups"],
                          users=stats["users"],
                          plays=stats["plays"],
                          uptime=uptime)
        try:
            await query.message.edit_caption(text, reply_markup=_start_buttons(me))
        except Exception:
            await query.message.edit_text(text, reply_markup=_start_buttons(me))

    await query.answer()


# ── Inline Mode ───────────────────────────────────────────────────────────────

@bot.on_inline_query()
async def inline_search(client: Client, query: InlineQuery):
    if not query.query.strip():
        return

    from core.downloader import search_youtube_list
    from utils.formatters import format_duration

    results_data = await search_youtube_list(query.query, 5)
    results = []

    for r in results_data:
        dur = format_duration(r.get("duration", 0))
        results.append(
            InlineQueryResultArticle(
                title=r["title"][:50],
                description=f"🎤 {r['artist'][:30]} | ⏱ {dur}",
                input_message_content=InputTextMessageContent(
                    f"🎵 **{r['title']}**\n"
                    f"🎤 {r['artist']}\n"
                    f"⏱ {dur}\n\n"
                    f"Use `/play {r['url']}` to play!"
                ),
                thumb_url=r.get("thumbnail") or "https://i.imgur.com/6vMdxAy.png",
            )
        )

    await query.answer(results, cache_time=30)
