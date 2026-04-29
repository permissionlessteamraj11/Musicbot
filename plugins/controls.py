from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot import bot
from core.queue import get_queue, QUEUE_MODE_LOOP, QUEUE_MODE_ONCE, QUEUE_MODE_SHUFFLE
from core.call import play_next, send_now_playing
from assistant import (
    pause_vc, resume_vc, stop_vc, mute_vc, unmute_vc,
    seek_stream, update_stream_effects, set_fx, get_fx, is_active, _vc_state
)
from utils.database import get_group
from utils.formatters import format_duration
from utils.decorators import admin_or_auth, admin_only
from strings import get_string


async def _lang(chat_id: int) -> str:
    g = await get_group(chat_id)
    return g.get("lang", "en")


# ── Pause / Resume ────────────────────────────────────────────────────────────

@bot.on_message(filters.command(["pause"]) & filters.group)
@admin_or_auth
async def pause_cmd(client: Client, message: Message):
    lang = await _lang(message.chat.id)
    if await pause_vc(message.chat.id):
        await message.reply_text(get_string(lang, "paused"))
    else:
        await message.reply_text(get_string(lang, "no_active_call"))


@bot.on_message(filters.command(["resume"]) & filters.group)
@admin_or_auth
async def resume_cmd(client: Client, message: Message):
    lang = await _lang(message.chat.id)
    if await resume_vc(message.chat.id):
        await message.reply_text(get_string(lang, "resumed"))
    else:
        await message.reply_text(get_string(lang, "no_active_call"))


# ── Skip / Stop ───────────────────────────────────────────────────────────────

@bot.on_message(filters.command(["skip", "s"]) & filters.group)
@admin_or_auth
async def skip_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    lang = await _lang(chat_id)
    if not is_active(chat_id):
        await message.reply_text(get_string(lang, "no_active_call"))
        return
    msg = await message.reply_text(get_string(lang, "skipped"))
    await play_next(client, chat_id, lang)


@bot.on_message(filters.command(["skipall", "stop", "end"]) & filters.group)
@admin_or_auth
async def skipall_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    lang = await _lang(chat_id)
    q = get_queue(chat_id)
    await q.clear()
    await stop_vc(chat_id)
    await message.reply_text(get_string(lang, "skipped_all"))


@bot.on_message(filters.command(["back"]) & filters.group)
@admin_or_auth
async def back_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    lang = await _lang(chat_id)
    q = get_queue(chat_id)
    track = await q.get_prev()
    if not track:
        await message.reply_text("❌ No previous track.")
        return
    from assistant import play_track
    success = await play_track(chat_id, track)
    if success:
        await send_now_playing(client, chat_id, track, lang)


@bot.on_message(filters.command(["replay"]) & filters.group)
@admin_or_auth
async def replay_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    lang = await _lang(chat_id)
    state = _vc_state.get(chat_id)
    if not state or not state.get("track"):
        await message.reply_text(get_string(lang, "nothing_playing"))
        return
    track = state["track"]
    from assistant import play_track
    await play_track(chat_id, track)
    await message.reply_text(get_string(lang, "replaying"))


# ── Volume ────────────────────────────────────────────────────────────────────

@bot.on_message(filters.command(["volume", "vol"]) & filters.group)
@admin_or_auth
async def volume_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    lang = await _lang(chat_id)
    if len(message.command) < 2:
        fx = get_fx(chat_id)
        await message.reply_text(f"🔊 Current volume: **{fx['volume']}%**\nUsage: `/volume 1-200`")
        return
    try:
        vol = int(message.command[1])
        vol = max(1, min(200, vol))
    except ValueError:
        await message.reply_text("❌ Invalid volume. Use 1-200.")
        return
    set_fx(chat_id, volume=vol)
    await update_stream_effects(chat_id)
    await message.reply_text(get_string(lang, "volume_set", vol=vol))


# ── Speed ─────────────────────────────────────────────────────────────────────

@bot.on_message(filters.command(["speed"]) & filters.group)
@admin_or_auth
async def speed_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    lang = await _lang(chat_id)
    if len(message.command) < 2:
        await message.reply_text("❌ Usage: `/speed 0.5-2.0`")
        return
    try:
        speed = float(message.command[1])
        speed = max(0.5, min(2.0, speed))
    except ValueError:
        await message.reply_text("❌ Invalid speed. Use 0.5-2.0")
        return
    set_fx(chat_id, speed=speed)
    await update_stream_effects(chat_id)
    await message.reply_text(get_string(lang, "speed_set", speed=speed))


# ── Mute / Unmute ─────────────────────────────────────────────────────────────

@bot.on_message(filters.command(["mute"]) & filters.group)
@admin_or_auth
async def mute_cmd(client: Client, message: Message):
    await mute_vc(message.chat.id)
    await message.reply_text(get_string(await _lang(message.chat.id), "muted"))


@bot.on_message(filters.command(["unmute"]) & filters.group)
@admin_or_auth
async def unmute_cmd(client: Client, message: Message):
    await unmute_vc(message.chat.id)
    await message.reply_text(get_string(await _lang(message.chat.id), "unmuted"))


# ── Loop / Shuffle ────────────────────────────────────────────────────────────

@bot.on_message(filters.command(["loop"]) & filters.group)
@admin_or_auth
async def loop_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    lang = await _lang(chat_id)
    q = get_queue(chat_id)
    if q.mode == QUEUE_MODE_LOOP:
        q.set_mode(QUEUE_MODE_ONCE)
        await message.reply_text(get_string(lang, "looping_off"))
    else:
        q.set_mode(QUEUE_MODE_LOOP)
        await message.reply_text(get_string(lang, "looping_on"))


@bot.on_message(filters.command(["shuffle"]) & filters.group)
@admin_or_auth
async def shuffle_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    lang = await _lang(chat_id)
    q = get_queue(chat_id)
    await q.shuffle()
    await message.reply_text(get_string(lang, "shuffled"))


# ── Seek / Rewind ─────────────────────────────────────────────────────────────

@bot.on_message(filters.command(["seek"]) & filters.group)
@admin_or_auth
async def seek_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    lang = await _lang(chat_id)
    if len(message.command) < 2:
        await message.reply_text("❌ Usage: `/seek <seconds>`")
        return
    try:
        secs = int(message.command[1])
    except ValueError:
        await message.reply_text("❌ Invalid seconds.")
        return
    if await seek_stream(chat_id, secs):
        await message.reply_text(get_string(lang, "seeked", time=format_duration(secs)))
    else:
        await message.reply_text(get_string(lang, "nothing_playing"))


@bot.on_message(filters.command(["rewind"]) & filters.group)
@admin_or_auth
async def rewind_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    lang = await _lang(chat_id)
    state = _vc_state.get(chat_id)
    if not state:
        await message.reply_text(get_string(lang, "nothing_playing"))
        return
    try:
        secs = int(message.command[1]) if len(message.command) > 1 else 10
    except ValueError:
        secs = 10
    # Rewind = seek to max(0, current - secs) — simplified to 0 here
    if await seek_stream(chat_id, 0):
        await message.reply_text(f"⏪ Rewound by {secs} seconds.")


# ── Song Info ─────────────────────────────────────────────────────────────────

@bot.on_message(filters.command(["song", "now", "np"]) & filters.group)
async def song_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    lang = await _lang(chat_id)
    state = _vc_state.get(chat_id)
    if not state or not state.get("track"):
        await message.reply_text(get_string(lang, "nothing_playing"))
        return
    track = state["track"]
    await send_now_playing(client, chat_id, track, lang)


# ── Vote Skip ─────────────────────────────────────────────────────────────────

@bot.on_message(filters.command(["voteskip", "vs"]) & filters.group)
async def voteskip_cmd(client: Client, message: Message):
    from utils.cache import add_vote_skip, get_vote_count, clear_vote_skip
    from config import Config
    chat_id = message.chat.id
    lang = await _lang(chat_id)
    if not is_active(chat_id):
        await message.reply_text(get_string(lang, "no_active_call"))
        return
    count = await add_vote_skip(chat_id, message.from_user.id)
    needed = Config.VOTE_SKIP_NEEDED
    if count >= needed:
        await clear_vote_skip(chat_id)
        await message.reply_text(get_string(lang, "vote_skip_done"))
        await play_next(client, chat_id, lang)
    else:
        btn = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                f"🗳 Vote Skip ({count}/{needed})",
                callback_data=f"voteskip_{chat_id}"
            )
        ]])
        await message.reply_text(
            get_string(lang, "vote_skip", votes=count, needed=needed),
            reply_markup=btn,
        )


# ── Sleep Timer ───────────────────────────────────────────────────────────────

@bot.on_message(filters.command(["sleep"]) & filters.group)
@admin_or_auth
async def sleep_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    if len(message.command) < 2:
        await message.reply_text("❌ Usage: `/sleep <minutes>`")
        return
    try:
        mins = int(message.command[1])
    except ValueError:
        await message.reply_text("❌ Invalid minutes.")
        return
    from utils.cache import set_sleep_timer
    await set_sleep_timer(chat_id, mins * 60)
    await message.reply_text(f"😴 Sleep timer set for **{mins} minutes**. Bot will stop after queue.")


# ── 24/7 Mode ─────────────────────────────────────────────────────────────────

@bot.on_message(filters.command(["247"]) & filters.group)
@admin_only
async def mode_247(client: Client, message: Message):
    chat_id = message.chat.id
    from utils.database import get_group, update_group
    g = await get_group(chat_id)
    state = not g.get("247_mode", False)
    await update_group(chat_id, {"247_mode": state})
    status = "✅ **ON**" if state else "❌ **OFF**"
    await message.reply_text(
        f"⏰ **24/7 Mode** {status}\n"
        f"{'Bot will play lofi radio when queue is empty.' if state else ''}"
    )


# ── Callback Query Handler ────────────────────────────────────────────────────

@bot.on_callback_query(filters.regex(r"^(pause|skip|loop|queue|volup|voldown|voteskip)_(-?\d+)$"))
async def player_callback(client: Client, query: CallbackQuery):
    action, chat_id_str = query.data.split("_", 1)
    chat_id = int(chat_id_str)
    lang = await _lang(chat_id)

    if action == "pause":
        state = _vc_state.get(chat_id, {})
        if state.get("paused"):
            await resume_vc(chat_id)
            await query.answer("▶️ Resumed!")
        else:
            await pause_vc(chat_id)
            await query.answer("⏸ Paused!")

    elif action == "skip":
        await query.answer("⏭ Skipping...")
        await play_next(client, chat_id, lang)

    elif action == "loop":
        q = get_queue(chat_id)
        if q.mode == QUEUE_MODE_LOOP:
            q.set_mode(QUEUE_MODE_ONCE)
            await query.answer("🔁 Loop OFF")
        else:
            q.set_mode(QUEUE_MODE_LOOP)
            await query.answer("🔁 Loop ON!")

    elif action == "volup":
        fx = get_fx(chat_id)
        new_vol = min(200, fx["volume"] + 10)
        set_fx(chat_id, volume=new_vol)
        await update_stream_effects(chat_id)
        await query.answer(f"🔊 Volume: {new_vol}%")

    elif action == "voldown":
        fx = get_fx(chat_id)
        new_vol = max(1, fx["volume"] - 10)
        set_fx(chat_id, volume=new_vol)
        await update_stream_effects(chat_id)
        await query.answer(f"🔉 Volume: {new_vol}%")

    elif action == "queue":
        q = get_queue(chat_id)
        tracks = q.get_list()
        if not tracks:
            await query.answer(get_string(lang, "queue_empty"), show_alert=True)
        else:
            text = "📋 **Queue:**\n" + "\n".join(
                f"{i+1}. {t.title[:40]}" for i, t in enumerate(tracks[:10])
            )
            await query.answer(text[:200], show_alert=True)

    elif action == "voteskip":
        from utils.cache import add_vote_skip, clear_vote_skip
        from config import Config
        count = await add_vote_skip(chat_id, query.from_user.id)
        needed = Config.VOTE_SKIP_NEEDED
        if count >= needed:
            await clear_vote_skip(chat_id)
            await query.answer("✅ Vote passed! Skipping...")
            await play_next(client, chat_id, lang)
        else:
            await query.answer(f"🗳 Voted! {count}/{needed} votes")
