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
        W, H = 800, 400
        img = Image.new("RGBA", (W, H), (8, 8, 12, 255))
        draw = ImageDraw.Draw(img)

        # Subtle geometric patterns
        for i in range(0, W, 40):
            draw.line([(i, 0), (i, H)], fill=(20, 20, 30), width=1)
        for i in range(0, H, 40):
            draw.line([(0, i), (W, i)], fill=(20, 20, 30), width=1)

        # Glow
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse([W//2-200, -100, W//2+200, 200], fill=(60, 60, 150, 40))
        img = Image.alpha_composite(img, glow)
        draw = ImageDraw.Draw(img)

        FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")
        def _font(name, size):
            try:
                return ImageFont.truetype(os.path.join(FONT_DIR, name), size)
            except Exception:
                return ImageFont.load_default()

        # Logo text
        draw.text((W // 2, 120), bot_name.upper(), font=_font("Montserrat-Bold.ttf", 48), fill=(255, 255, 255), anchor="mm")
        draw.text((W // 2, 175), "HIGH-PERFORMANCE AUDIO STREAMING ENGINE",
                  font=_font("Montserrat-Regular.ttf", 14), fill=(120, 120, 180), anchor="mm")

        # Divider
        draw.line([W//2-100, 210, W//2+100, 210], fill=(100, 100, 255, 100), width=2)

        # Stats
        y = 260
        stats_data = [
            (f"{stats['groups']}", "ACTIVE NODES"),
            (f"{stats['plays']}", "TOTAL STREAMS"),
            (uptime.upper(), "SYSTEM UPTIME"),
        ]

        for i, (val, label) in enumerate(stats_data):
            x = W // 4 * (i + 1)
            draw.text((x, y), val, font=_font("Montserrat-Bold.ttf", 22), fill=(255, 255, 255), anchor="mm")
            draw.text((x, y + 35), label, font=_font("Montserrat-Regular.ttf", 11), fill=(100, 100, 140), anchor="mm")

        buf = io.BytesIO()
        img.convert("RGB").save(buf, "PNG")
        buf.seek(0)
        return buf.read()

    return await asyncio.get_event_loop().run_in_executor(None, _draw)


def _start_buttons(me) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "Initialize System",
                url=f"https://t.me/{me.username}?startgroup=true",
            ),
            InlineKeyboardButton("Technical Support", url=Config.SUPPORT_LINK),
        ],
        [
            InlineKeyboardButton("Statistics", callback_data="start_stats"),
            InlineKeyboardButton("Documentation", callback_data="start_help"),
        ],
        [
            InlineKeyboardButton("System Owner", url=f"tg://user?id={Config.OWNER_ID}"),
            InlineKeyboardButton("Source Code", url=Config.UPSTREAM_REPO),
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
        f"System Online: **{Config.BOT_NAME}** initialized.\n"
        f"Execute `/play <query>` to begin streaming.\n"
        f"Access `/help` for system documentation.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Documentation", callback_data="start_help")
        ]]),
    )


@bot.on_message(filters.command(["help", "h"]))
async def help_cmd(client: Client, message: Message):
    text = get_string("en", "help_text", bot_name=Config.BOT_NAME)
    await message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Initialize System",
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
                InlineKeyboardButton("Return", callback_data="start_back")
            ]]),
        )

    elif action == "help":
        text = get_string("en", "help_text", bot_name=Config.BOT_NAME)
        try:
            await query.message.edit_caption(
                text,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Return", callback_data="start_back")
                ]]),
            )
        except Exception:
            await query.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Return", callback_data="start_back")
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
                description=f"Performer: {r['artist'][:30]} | Duration: {dur}",
                input_message_content=InputTextMessageContent(
                    f"**{r['title']}**\n"
                    f"Performer: {r['artist']}\n"
                    f"Duration: {dur}\n\n"
                    f"Execute `/play {r['url']}` to initialize stream."
                ),
                thumb_url=r.get("thumbnail") or "https://i.imgur.com/6vMdxAy.png",
            )
        )

    await query.answer(results, cache_time=30)
