import asyncio
import re
import yt_dlp
from config import Config
from utils.cache import cache_audio_url, get_cached_audio
from utils.logger import LOGGER

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
    _sp = spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(
            client_id=Config.SPOTIFY_CLIENT_ID,
            client_secret=Config.SPOTIFY_CLIENT_SECRET,
        )
    ) if Config.SPOTIFY_CLIENT_ID else None
except Exception:
    _sp = None

YTDLP_OPTS = {
    "format": "bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "extract_flat": False,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "320",
        }
    ],
    "socket_timeout": 15,
    "retries": 3,
}

PLAYLIST_OPTS = {
    **YTDLP_OPTS,
    "noplaylist": False,
    "extract_flat": True,
}

SEARCH_OPTS = {
    "format": "bestaudio",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "extract_flat": True,
    "default_search": "ytsearch10",
}


def _is_url(text: str) -> bool:
    return text.startswith(("http://", "https://", "www."))


def _is_spotify(url: str) -> bool:
    return "spotify.com" in url


def _is_youtube_playlist(url: str) -> bool:
    return "playlist?list=" in url or "&list=" in url


def _cache_key(query: str) -> str:
    return re.sub(r"[^a-z0-9]", "_", query.lower())[:100]


async def _run_ydl(opts: dict, query: str) -> dict | None:
    def _extract():
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(query, download=False)

    try:
        return await asyncio.get_event_loop().run_in_executor(None, _extract)
    except Exception as e:
        LOGGER.error(f"yt-dlp error: {e}")
        return None


async def get_spotify_track(url: str) -> dict | None:
    """Convert Spotify track URL → YouTube search result."""
    if not _sp:
        return None
    try:
        track_id = url.split("/track/")[-1].split("?")[0]
        track = await asyncio.get_event_loop().run_in_executor(
            None, lambda: _sp.track(track_id)
        )
        name = track["name"]
        artist = track["artists"][0]["name"]
        thumb = track["album"]["images"][0]["url"] if track["album"]["images"] else None
        duration = track["duration_ms"] // 1000
        query = f"{name} {artist}"
        result = await search_youtube(query)
        if result:
            result["title"] = f"{name} — {artist}"
            result["artist"] = artist
            result["thumbnail"] = thumb or result.get("thumbnail")
            result["duration"] = duration
        return result
    except Exception as e:
        LOGGER.error(f"Spotify track error: {e}")
        return None


async def get_spotify_playlist(url: str) -> list:
    """Return list of track dicts from Spotify playlist/album."""
    if not _sp:
        return []
    tracks = []
    try:
        if "/playlist/" in url:
            pid = url.split("/playlist/")[-1].split("?")[0]
            results = await asyncio.get_event_loop().run_in_executor(
                None, lambda: _sp.playlist_items(pid)
            )
            items = results["items"]
        elif "/album/" in url:
            aid = url.split("/album/")[-1].split("?")[0]
            results = await asyncio.get_event_loop().run_in_executor(
                None, lambda: _sp.album_tracks(aid)
            )
            items = [{"track": t} for t in results["items"]]
        else:
            return []

        for item in items:
            t = item.get("track") or item
            if not t:
                continue
            name = t.get("name", "Unknown")
            artist = t["artists"][0]["name"] if t.get("artists") else "Unknown"
            duration = t.get("duration_ms", 0) // 1000
            tracks.append({
                "title": f"{name} — {artist}",
                "artist": artist,
                "duration": duration,
                "query": f"{name} {artist}",
                "source": "spotify",
                "thumbnail": None,
                "url": None,  # Will be resolved on play
            })
    except Exception as e:
        LOGGER.error(f"Spotify playlist error: {e}")
    return tracks


async def search_youtube(query: str, limit: int = 10) -> dict | None:
    """Search YouTube and return first result."""
    cache_k = _cache_key(query)
    cached = await get_cached_audio(cache_k)
    if cached:
        LOGGER.debug(f"Cache hit: {query}")
        return cached

    info = await _run_ydl(SEARCH_OPTS, f"ytsearch:{query}")
    if not info or not info.get("entries"):
        return None

    entry = info["entries"][0]
    data = {
        "title": entry.get("title", "Unknown"),
        "url": f"https://youtube.com/watch?v={entry['id']}",
        "duration": entry.get("duration", 0),
        "thumbnail": entry.get("thumbnail", ""),
        "artist": entry.get("uploader", "Unknown"),
        "source": "youtube",
    }
    return data


async def search_youtube_list(query: str, limit: int = 10) -> list:
    """Return multiple YouTube search results."""
    info = await _run_ydl(SEARCH_OPTS, f"ytsearch{limit}:{query}")
    if not info or not info.get("entries"):
        return []
    results = []
    for e in info["entries"][:limit]:
        results.append({
            "title": e.get("title", "Unknown"),
            "url": f"https://youtube.com/watch?v={e['id']}",
            "duration": e.get("duration", 0),
            "thumbnail": e.get("thumbnail", ""),
            "artist": e.get("uploader", "Unknown"),
            "source": "youtube",
        })
    return results


async def get_stream_url(video_url: str) -> dict | None:
    """Resolve final audio stream URL for a YouTube video."""
    cache_k = _cache_key(video_url)
    cached = await get_cached_audio(cache_k)
    if cached and cached.get("stream_url"):
        return cached

    opts = {**YTDLP_OPTS, "noplaylist": True}
    info = await _run_ydl(opts, video_url)
    if not info:
        return None

    # Find best audio format
    stream_url = info.get("url")
    if not stream_url and info.get("formats"):
        for f in reversed(info["formats"]):
            if f.get("acodec") != "none" and f.get("url"):
                stream_url = f["url"]
                break

    if not stream_url:
        return None

    data = {
        "title": info.get("title", "Unknown"),
        "stream_url": stream_url,
        "duration": info.get("duration", 0),
        "thumbnail": info.get("thumbnail", ""),
        "artist": info.get("uploader", "Unknown"),
        "source": "youtube",
        "url": video_url,
    }
    await cache_audio_url(cache_k, data)
    return data


async def get_youtube_playlist(url: str) -> list:
    """Return list of video entries from YouTube playlist."""
    info = await _run_ydl(PLAYLIST_OPTS, url)
    if not info or not info.get("entries"):
        return []
    tracks = []
    for e in info["entries"]:
        if not e:
            continue
        tracks.append({
            "title": e.get("title", "Unknown"),
            "url": f"https://youtube.com/watch?v={e['id']}",
            "duration": e.get("duration", 0),
            "thumbnail": e.get("thumbnail", ""),
            "artist": e.get("uploader", "Unknown"),
            "source": "youtube",
        })
    return tracks


async def resolve_query(query: str) -> dict | None:
    """Smart resolver: handles URLs, Spotify, YouTube search."""
    q = query.strip()

    if _is_spotify(q):
        if "/track/" in q:
            return await get_spotify_track(q)
        return None  # Playlists handled separately

    if _is_url(q):
        data = await get_stream_url(q)
        return data

    # Plain text search
    result = await search_youtube(q)
    if not result:
        return None
    stream = await get_stream_url(result["url"])
    if stream:
        stream["title"] = result["title"]
        stream["thumbnail"] = result["thumbnail"]
        stream["artist"] = result["artist"]
    return stream
