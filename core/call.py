import asyncio
from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.queue import get_queue, Track
from core.downloader import resolve_query
from assistant import play_track, stop_vc, get_fx, is_active
from utils.thumbnail import make_now_playing_card
from utils.formatters import format_duration
from utils.database import log_play, increment_plays, update_group
from utils.cache import check_sleep_timer
from utils.logger import LOGGER
from config import Config
from strings import get_string


def _player_buttons(chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏸ Pause", callback_data=f"pause_{chat_id}"),
            InlineKeyboardButton("⏭ Skip", callback_data=f"skip_{chat_id}"),
            InlineKeyboardButton("🔁 Loop", callback_data=f"loop_{chat_id}"),
        ],
        [
            InlineKeyboardButton("📋 Queue", callback_data=f"queue_{chat_id}"),
            InlineKeyboardButton("🔊 Vol+", callback_data=f"volup_{chat_id}"),
            InlineKeyboardButton("🔉 Vol-", callback_data=f"voldown_{chat_id}"),
        ],
    ])


async def send_now_playing(client: Client, chat_id: int, track: Track, lang: str = "en"):
    try:
        card_path = await make_now_playing_card(
            title=track.title,
            artist=track.artist,
            duration=track.duration,
            requester=track.requester_name,
            thumb_url=track.thumbnail,
        )
        caption = (
            f"🎵 **Now Playing**\n\n"
            f"**{track.title}**\n"
            f"🎤 {track.artist}\n"
            f"⏱ {format_duration(track.duration)}\n"
            f"👤 {track.requester_name}"
        )
        await client.send_photo(
            chat_id,
            photo=card_path,
            caption=caption,
            reply_markup=_player_buttons(chat_id),
        )
    except Exception as e:
        LOGGER.error(f"Now playing card error: {e}")
        # Fallback text message
        await client.send_message(
            chat_id,
            f"🎵 **Now Playing:** {track.title}\n🎤 {track.artist}\n⏱ {format_duration(track.duration)}",
            reply_markup=_player_buttons(chat_id),
        )


async def play_next(client: Client, chat_id: int, lang: str = "en"):
    """Called when current track ends or skip is requested."""
    q = get_queue(chat_id)

    # Check sleep timer
    if await check_sleep_timer(chat_id):
        await stop_vc(chat_id)
        await q.clear()
        try:
            await client.send_message(chat_id, "😴 Sleep timer expired. Stopped playback.")
        except Exception:
            pass
        return

    # Check 24/7 lofi mode if queue empty
    from utils.database import get_group
    group = await get_group(chat_id)

    track = await q.get_next()

    if not track:
        if group.get("247_mode"):
            # Play lofi radio
            lofi_url = "https://www.youtube.com/watch?v=jfKfPfyJRdk"  # lofi girl
            data = await resolve_query(lofi_url)
            if data:
                track = Track(
                    title="Lofi Hip Hop Radio 🎵",
                    url=lofi_url,
                    stream_url=data["stream_url"],
                    duration=0,
                    thumbnail=data.get("thumbnail", ""),
                    artist="Lofi Girl",
                    requester_id=0,
                    requester_name="24/7 Mode",
                    source="youtube",
                )
                await q.set_current(track)
            else:
                await stop_vc(chat_id)
                return
        else:
            await stop_vc(chat_id)
            try:
                await client.send_message(chat_id, "✅ Queue ended. Left voice chat.")
            except Exception:
                pass
            return

    # Resolve stream URL if needed
    if not track.stream_url:
        data = await resolve_query(track.url or track.title)
        if not data:
            LOGGER.warning(f"Could not resolve: {track.title}")
            await play_next(client, chat_id, lang)
            return
        track.stream_url = data["stream_url"]
        track.thumbnail = data.get("thumbnail", track.thumbnail)
        track.duration = data.get("duration", track.duration)

    # Pre-fetch next track
    asyncio.create_task(_prefetch_next(q))

    success = await play_track(chat_id, track)
    if not success:
        LOGGER.error(f"play_track failed for {track.title}, skipping...")
        await play_next(client, chat_id, lang)
        return

    await send_now_playing(client, chat_id, track, lang)
    await log_play(chat_id, track.requester_id, track.title)
    await increment_plays(track.requester_id)


async def _prefetch_next(q):
    """Background task to pre-resolve the next track's stream URL."""
    upcoming = q.get_list()
    if not upcoming:
        return
    next_track = upcoming[0]
    if not next_track.stream_url and next_track.url:
        try:
            data = await resolve_query(next_track.url)
            if data:
                next_track.stream_url = data["stream_url"]
                LOGGER.debug(f"Pre-fetched: {next_track.title}")
        except Exception:
            pass


async def handle_stream_end(client: Client, chat_id: int):
    """Triggered when PyTgCalls reports stream ended."""
    from utils.database import get_group
    group = await get_group(chat_id)
    lang = group.get("lang", "en")
    await play_next(client, chat_id, lang)
