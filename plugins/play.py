import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from bot import bot
from config import Config
from core.queue import get_queue, Track, QUEUE_MODE_ONCE
from core.downloader import (
    resolve_query, get_youtube_playlist, get_spotify_playlist,
    search_youtube_list, _is_spotify, _is_youtube_playlist, _is_url
)
from core.call import play_next, send_now_playing
from assistant import is_active, play_track
from utils.database import get_group, get_blacklist, increment_plays, log_play
from utils.formatters import format_duration
from utils.decorators import admin_or_auth, rate_limited, maintenance_check
from utils.logger import LOGGER
from strings import get_string


def _make_track(data: dict, user) -> Track:
    return Track(
        title=data.get("title", "Unknown"),
        url=data.get("url", ""),
        stream_url=data.get("stream_url", ""),
        duration=data.get("duration", 0),
        thumbnail=data.get("thumbnail", ""),
        artist=data.get("artist", "Unknown"),
        requester_id=user.id,
        requester_name=user.first_name,
        source=data.get("source", "youtube"),
    )


async def _get_lang(chat_id: int) -> str:
    g = await get_group(chat_id)
    return g.get("lang", "en")


@bot.on_message(filters.command(["play", "p"]) & filters.group)
@maintenance_check
@rate_limited
@admin_or_auth
async def play_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    lang = await _get_lang(chat_id)
    q = get_queue(chat_id)

    # Get query
    if len(message.command) < 2:
        if message.reply_to_message and (
            message.reply_to_message.audio or message.reply_to_message.voice
        ):
            return await _play_file(client, message, message.reply_to_message)
        await message.reply_text("Error: Missing parameters. Usage: `/play <query or URL>`")
        return

    query = " ".join(message.command[1:])
    status = await message.reply_text(get_string(lang, "searching", query=query))

    # Spotify playlist/album
    if _is_spotify(query):
        if "/playlist/" in query or "/album/" in query:
            await _play_spotify_playlist(client, message, query, status, lang)
            return

    # YouTube playlist
    if _is_youtube_playlist(query):
        await _play_youtube_playlist(client, message, query, status, lang)
        return

    # Single track
    await status.edit_text(get_string(lang, "downloading"))
    data = await resolve_query(query)

    if not data:
        await status.edit_text(get_string(lang, "no_results", query=query))
        return

    # Check blacklist
    blacklist = await get_blacklist(chat_id)
    if any(b in data["title"].lower() for b in blacklist):
        await status.edit_text(get_string(lang, "song_blacklisted"))
        return

    # Check duration
    if data.get("duration", 0) > Config.MAX_DURATION:
        await status.edit_text(
            get_string(lang, "duration_too_long", max=format_duration(Config.MAX_DURATION))
        )
        return

    # Check queue limit
    g = await get_group(chat_id)
    limit = g.get("queue_limit", Config.MAX_QUEUE_SIZE)

    track = _make_track(data, message.from_user)

    if not is_active(chat_id) and q.is_empty:
        # Play immediately
        await q.set_current(track)
        success = await play_track(chat_id, track)
        if success:
            await status.delete()
            await send_now_playing(client, chat_id, track, lang)
        else:
            await status.edit_text("❌ Failed to join voice chat. Make sure I'm in the VC!")
    else:
        pos = await q.add(track)
        await status.edit_text(
            get_string(lang, "added_to_queue",
                       pos=pos, title=data["title"],
                       duration=format_duration(data.get("duration", 0)))
        )


@bot.on_message(filters.command(["vplay", "vc"]) & filters.group)
@maintenance_check
@rate_limited
@admin_or_auth
async def vplay_cmd(client: Client, message: Message):
    """Play video stream in VC."""
    await message.reply_text("System: Video stream initialization initiated.")
    # Re-use play logic — PyTgCalls handles video automatically with VideoStream
    # Forward to play_cmd
    message.command[0] = "play"
    await play_cmd(client, message)


@bot.on_message(filters.command(["fplay"]) & filters.group)
@maintenance_check
@admin_or_auth
async def fplay_cmd(client: Client, message: Message):
    """Play uploaded audio/video file."""
    reply = message.reply_to_message
    if not reply or not (reply.audio or reply.voice or reply.video or reply.document):
        await message.reply_text("Error: Please reply to a valid media file with `/fplay`")
        return
    await _play_file(client, message, reply)


async def _play_file(client: Client, message: Message, file_msg: Message):
    chat_id = message.chat.id
    lang = await _get_lang(chat_id)
    status = await message.reply_text("⬇️ Downloading file...")

    media = file_msg.audio or file_msg.voice or file_msg.video or file_msg.document
    if not media:
        await status.edit_text("❌ No media found.")
        return

    try:
        path = await file_msg.download()
        title = getattr(media, "title", None) or getattr(media, "file_name", "Audio File") or "Audio File"
        duration = getattr(media, "duration", 0) or 0

        track = Track(
            title=title,
            url=path,
            stream_url=path,
            duration=duration,
            thumbnail="",
            artist="Local File",
            requester_id=message.from_user.id,
            requester_name=message.from_user.first_name,
            source="file",
        )

        q = get_queue(chat_id)
        if not is_active(chat_id) and q.is_empty:
            await q.set_current(track)
            success = await play_track(chat_id, track)
            if success:
                await status.delete()
                await send_now_playing(client, chat_id, track, lang)
            else:
                await status.edit_text("❌ Failed to play file.")
        else:
            pos = await q.add(track)
            await status.edit_text(f"➕ Added **{title}** to queue [#{pos}]")
    except Exception as e:
        LOGGER.error(f"fplay error: {e}")
        await status.edit_text(f"❌ Error: {e}")


@bot.on_message(filters.command(["livestream", "live"]) & filters.group)
@maintenance_check
@admin_or_auth
async def livestream_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    lang = await _get_lang(chat_id)
    if len(message.command) < 2:
        await message.reply_text("❌ Usage: `/livestream <url>`")
        return
    url = message.command[1]
    status = await message.reply_text("📡 Connecting to live stream...")
    data = await resolve_query(url)
    if not data:
        await status.edit_text("❌ Could not connect to stream.")
        return
    track = _make_track(data, message.from_user)
    track.duration = 0  # Live
    q = get_queue(chat_id)
    await q.set_current(track)
    success = await play_track(chat_id, track)
    if success:
        await status.delete()
        await message.reply_text(
            get_string(lang, "live_stream", title=track.title)
        )
    else:
        await status.edit_text("❌ Failed to start live stream.")


@bot.on_message(filters.command(["radio"]) & filters.group)
@admin_or_auth
async def radio_cmd(client: Client, message: Message):
    STATIONS = {
        "lofi": "https://www.youtube.com/watch?v=jfKfPfyJRdk",
        "jazz": "https://www.youtube.com/watch?v=Dx5qFachd3A",
        "classical": "https://www.youtube.com/watch?v=4To8FAAfGas",
        "bollywood": "https://www.youtube.com/watch?v=u4YbOCfWM0A",
        "edm": "https://www.youtube.com/watch?v=4xDzrJKXOOY",
        "pop": "https://www.youtube.com/watch?v=ZbZSe6N_BXs",
    }
    if len(message.command) < 2:
        station_list = "\n".join(f"  • `{k}`" for k in STATIONS)
        await message.reply_text(f"📻 **Available Radio Stations:**\n\n{station_list}\n\nUsage: `/radio lofi`")
        return
    name = message.command[1].lower()
    url = STATIONS.get(name)
    if not url:
        await message.reply_text(f"❌ Unknown station. Available: {', '.join(STATIONS)}")
        return
    message.command = ["livestream", url]
    await livestream_cmd(client, message)


@bot.on_message(filters.command(["playlist"]) & filters.group)
@maintenance_check
@admin_or_auth
async def playlist_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    lang = await _get_lang(chat_id)
    if len(message.command) < 2:
        await message.reply_text("❌ Usage: `/playlist <url or name>`")
        return
    query = " ".join(message.command[1:])
    status = await message.reply_text("📋 Loading playlist...")

    tracks_data = []
    if _is_spotify(query) and ("/playlist/" in query or "/album/" in query):
        tracks_data = await get_spotify_playlist(query)
    elif _is_url(query):
        tracks_data = await get_youtube_playlist(query)
    else:
        # Search as YouTube playlist name
        tracks_data = await get_youtube_playlist(f"ytsearch:{query} playlist")

    if not tracks_data:
        await status.edit_text("❌ No tracks found in playlist.")
        return

    q = get_queue(chat_id)
    tracks = [_make_track(t, message.from_user) for t in tracks_data]
    await q.add_many(tracks)

    await status.edit_text(
        f"✅ **{len(tracks)} tracks** added to queue!\n"
        f"▶️ First: **{tracks[0].title}**"
    )

    if not is_active(chat_id):
        await play_next(client, chat_id, lang)


@bot.on_message(filters.command(["search", "find"]) & filters.group)
@admin_or_auth
async def search_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    lang = await _get_lang(chat_id)
    if len(message.command) < 2:
        await message.reply_text("❌ Usage: `/search <song name>`")
        return
    query = " ".join(message.command[1:])
    status = await message.reply_text(f"🔍 Searching for `{query}`...")

    results = await search_youtube_list(query, 8)
    if not results:
        await status.edit_text("❌ No results found.")
        return

    text = f"🔎 **Search Results for:** `{query}`\n\n"
    for i, r in enumerate(results, 1):
        dur = format_duration(r.get("duration", 0))
        text += f"`{i}.` **{r['title'][:45]}**\n    ⏱ {dur} | 🎤 {r['artist'][:25]}\n\n"

    text += "Reply with a number to play that track."

    await status.edit_text(text)

    # Wait for user's number response
    try:
        resp = await client.listen(
            chat_id=chat_id,
            filters=filters.text & filters.user(message.from_user.id),
            timeout=30,
        )
        choice = int(resp.text.strip())
        if 1 <= choice <= len(results):
            selected = results[choice - 1]
            message.command = ["play", selected["url"]]
            await play_cmd(client, message)
        else:
            await message.reply_text("Error: Invalid selection. Please provide a number from the list.")
    except asyncio.TimeoutError:
        await message.reply_text("System: Search session timed out.")
    except ValueError:
        await message.reply_text("Error: Numerical input required.")


async def _play_youtube_playlist(client, message, url, status, lang):
    chat_id = message.chat.id
    await status.edit_text("⬇️ Loading YouTube playlist...")
    tracks_data = await get_youtube_playlist(url)
    if not tracks_data:
        await status.edit_text("❌ Empty or invalid playlist.")
        return
    q = get_queue(chat_id)
    tracks = [_make_track(t, message.from_user) for t in tracks_data]
    await q.add_many(tracks)
    await status.edit_text(
        f"✅ **{len(tracks)} tracks** queued!\n▶️ First: **{tracks[0].title}**"
    )
    if not is_active(chat_id):
        await play_next(client, chat_id, lang)


async def _play_spotify_playlist(client, message, url, status, lang):
    chat_id = message.chat.id
    await status.edit_text("🎵 Loading Spotify playlist...")
    tracks_data = await get_spotify_playlist(url)
    if not tracks_data:
        await status.edit_text("❌ Empty or invalid Spotify playlist.")
        return
    q = get_queue(chat_id)
    tracks = [_make_track(t, message.from_user) for t in tracks_data]
    await q.add_many(tracks)
    await status.edit_text(
        f"✅ **{len(tracks)} Spotify tracks** queued!\n🎵 First: **{tracks[0].title}**"
    )
    if not is_active(chat_id):
        await play_next(client, chat_id, lang)
