from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot import bot
from core.queue import get_queue
from utils.formatters import format_duration
from utils.decorators import admin_or_auth
from utils.database import get_group


async def _lang(cid): 
    g = await get_group(cid); return g.get("lang", "en")

QUEUE_PAGE_SIZE = 5


def _queue_keyboard(chat_id: int, page: int, total_pages: int) -> InlineKeyboardMarkup:
    btns = []
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"qpage_{chat_id}_{page-1}"))
    nav.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"qpage_{chat_id}_{page+1}"))
    if nav:
        btns.append(nav)
    btns.append([InlineKeyboardButton("🗑 Clear Queue", callback_data=f"clearq_{chat_id}")])
    return InlineKeyboardMarkup(btns)


def _render_queue_page(chat_id: int, tracks: list, current, page: int, page_size: int) -> str:
    total = len(tracks)
    total_pages = max(1, (total + page_size - 1) // page_size)
    start = (page - 1) * page_size
    end = start + page_size
    page_tracks = tracks[start:end]

    text = "📋 **Queue**\n\n"
    if current:
        text += f"▶️ **Now:** {current.title[:40]}\n    ⏱ {format_duration(current.duration)}\n\n"

    for i, t in enumerate(page_tracks, start=start+1):
        text += f"`{i}.` **{t.title[:40]}**\n    ⏱ {format_duration(t.duration)} | 👤 {t.requester_name}\n\n"

    text += f"📊 Total: {total} tracks | Page {page}/{total_pages}"
    return text, total_pages


@bot.on_message(filters.command(["queue", "q"]) & filters.group)
async def queue_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    q = get_queue(chat_id)
    tracks = q.get_list()
    current = q.current

    if not tracks and not current:
        from strings import get_string
        lang = await _lang(chat_id)
        await message.reply_text(get_string(lang, "queue_empty"))
        return

    text, total_pages = _render_queue_page(chat_id, tracks, current, 1, QUEUE_PAGE_SIZE)
    await message.reply_text(
        text,
        reply_markup=_queue_keyboard(chat_id, 1, total_pages) if total_pages > 1 else None,
    )


@bot.on_callback_query(filters.regex(r"^qpage_(-?\d+)_(\d+)$"))
async def queue_page_cb(client: Client, query: CallbackQuery):
    chat_id = int(query.matches[0].group(1))
    page = int(query.matches[0].group(2))
    q = get_queue(chat_id)
    tracks = q.get_list()
    current = q.current
    if not tracks and not current:
        await query.answer("Queue is empty!", show_alert=True)
        return
    text, total_pages = _render_queue_page(chat_id, tracks, current, page, QUEUE_PAGE_SIZE)
    await query.message.edit_text(
        text,
        reply_markup=_queue_keyboard(chat_id, page, total_pages),
    )
    await query.answer()


@bot.on_callback_query(filters.regex(r"^clearq_(-?\d+)$"))
@admin_or_auth
async def clear_queue_cb(client: Client, query: CallbackQuery):
    chat_id = int(query.matches[0].group(1))
    q = get_queue(chat_id)
    await q.clear()
    await query.message.edit_text("🗑 **Queue cleared!**")
    await query.answer("Queue cleared!")


@bot.on_message(filters.command(["remove", "rm"]) & filters.group)
@admin_or_auth
async def remove_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    if len(message.command) < 2:
        await message.reply_text("❌ Usage: `/remove <position>`")
        return
    try:
        pos = int(message.command[1])
    except ValueError:
        await message.reply_text("❌ Invalid position.")
        return
    q = get_queue(chat_id)
    track = await q.remove(pos)
    if track:
        await message.reply_text(f"🗑 Removed **#{pos}: {track.title}** from queue.")
    else:
        await message.reply_text("❌ Invalid position.")


@bot.on_message(filters.command(["move"]) & filters.group)
@admin_or_auth
async def move_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    if len(message.command) < 3:
        await message.reply_text("❌ Usage: `/move <from> <to>`")
        return
    try:
        p1 = int(message.command[1])
        p2 = int(message.command[2])
    except ValueError:
        await message.reply_text("❌ Invalid positions.")
        return
    q = get_queue(chat_id)
    if await q.move(p1, p2):
        await message.reply_text(f"✅ Moved track from **#{p1}** to **#{p2}**.")
    else:
        await message.reply_text("❌ Invalid positions.")


@bot.on_message(filters.command(["clearqueue", "cq"]) & filters.group)
@admin_or_auth
async def clearqueue_cmd(client: Client, message: Message):
    q = get_queue(message.chat.id)
    await q.clear()
    await message.reply_text("🗑 **Queue cleared!**")


@bot.on_message(filters.command(["queuetype", "qt"]) & filters.group)
@admin_or_auth
async def queuetype_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    if len(message.command) < 2:
        await message.reply_text("❌ Usage: `/queuetype loop|once|shuffle`")
        return
    mode = message.command[1].lower()
    q = get_queue(chat_id)
    valid = {"loop", "once", "shuffle"}
    if mode not in valid:
        await message.reply_text(f"❌ Invalid mode. Choose: {', '.join(valid)}")
        return
    q.set_mode(mode)
    icons = {"loop": "🔁", "once": "➡️", "shuffle": "🔀"}
    await message.reply_text(f"{icons[mode]} Queue mode set to **{mode.upper()}**")


@bot.on_message(filters.command(["history"]) & filters.group)
async def history_cmd(client: Client, message: Message):
    from utils.database import get_recent_plays
    chat_id = message.chat.id
    plays = await get_recent_plays(chat_id, 10)
    if not plays:
        await message.reply_text("📭 No play history yet.")
        return
    text = "📜 **Recent Plays:**\n\n"
    for i, p in enumerate(plays, 1):
        text += f"`{i}.` {p['song'][:40]}\n"
    await message.reply_text(text)
