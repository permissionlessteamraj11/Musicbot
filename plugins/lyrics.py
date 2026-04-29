import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from bot import bot
from assistant import _vc_state
from config import Config
from utils.database import get_group

try:
    import lyricsgenius
    _genius = lyricsgenius.Genius(
        Config.GENIUS_API_TOKEN,
        timeout=10,
        skip_non_songs=True,
        excluded_terms=["(Remix)", "(Live)"],
        verbose=False,
    ) if Config.GENIUS_API_TOKEN else None
except Exception:
    _genius = None


async def _lang(cid):
    g = await get_group(cid); return g.get("lang", "en")


async def _fetch_lyrics(song: str) -> str | None:
    if not _genius:
        return None
    try:
        def _get():
            s = _genius.search_song(song)
            return s.lyrics[:4000] if s else None
        return await asyncio.get_event_loop().run_in_executor(None, _get)
    except Exception:
        return None


def _split_lyrics(text: str, chunk: int = 3500) -> list[str]:
    parts = []
    while text:
        parts.append(text[:chunk])
        text = text[chunk:]
    return parts


@bot.on_message(filters.command(["lyrics", "ly"]) & filters.group)
async def lyrics_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    if len(message.command) > 1:
        query = " ".join(message.command[1:])
    else:
        state = _vc_state.get(chat_id)
        if state and state.get("track"):
            query = state["track"].title
        else:
            await message.reply_text("❌ Nothing playing. Usage: `/lyrics <song name>`")
            return

    status = await message.reply_text(f"🔍 Fetching lyrics for **{query}**...")

    if not _genius:
        await status.edit_text(
            "❌ Genius API not configured.\n"
            "Set `GENIUS_API_TOKEN` in your `.env` file."
        )
        return

    lyrics = await _fetch_lyrics(query)

    if not lyrics:
        await status.edit_text(f"❌ Lyrics not found for **{query}**.")
        return

    # Clean up genius formatting
    lyrics = lyrics.replace("\\n", "\n").strip()

    chunks = _split_lyrics(lyrics)
    await status.delete()

    for i, chunk in enumerate(chunks):
        header = f"🎵 **{query}** — Lyrics\n\n" if i == 0 else ""
        footer = f"\n\n`Page {i+1}/{len(chunks)}`" if len(chunks) > 1 else ""
        await message.reply_text(f"{header}{chunk}{footer}")


@bot.on_message(filters.command(["suggest"]) & filters.group)
async def suggest_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    state = _vc_state.get(chat_id)
    if not state or not state.get("track"):
        await message.reply_text("❌ Nothing playing right now.")
        return

    current = state["track"]
    status = await message.reply_text(f"🤔 Finding songs similar to **{current.title}**...")

    from core.downloader import search_youtube_list
    query = f"songs like {current.title} {current.artist}"
    results = await search_youtube_list(query, 5)

    if not results:
        await status.edit_text("❌ Could not find suggestions.")
        return

    from utils.formatters import format_duration
    text = f"💡 **Suggestions based on:**\n🎵 {current.title}\n\n"
    for i, r in enumerate(results, 1):
        text += (
            f"`{i}.` **{r['title'][:45]}**\n"
            f"    🎤 {r['artist'][:30]} | ⏱ {format_duration(r.get('duration', 0))}\n\n"
        )
    text += "Use `/play <title>` to play any of these!"
    await status.edit_text(text)
