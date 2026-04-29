import asyncio
import subprocess
from typing import Optional
from pyrogram import Client
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality
from pytgcalls.exceptions import NotInCallError, AlreadyJoinedError
from config import Config
from core.effects import build_ffmpeg_cmd
from core.queue import get_queue, Track
from utils.logger import LOGGER

# ── Assistant Pool ─────────────────────────────────────────────────────────────

class Assistant:
    def __init__(self, session: str, index: int):
        self.index = index
        self.client = Client(
            f"assistant_{index}",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            session_string=session,
        )
        self.calls = PyTgCalls(self.client)
        self.active_chats: set[int] = set()
        self.started = False

    async def start(self):
        if not self.started:
            await self.client.start()
            await self.calls.start()
            self.started = True
            LOGGER.info(f"Assistant {self.index} started.")

    async def stop(self):
        if self.started:
            await self.calls.stop()
            await self.client.stop()
            self.started = False

    def is_busy(self, chat_id: int) -> bool:
        return chat_id in self.active_chats

    async def join_vc(self, chat_id: int):
        self.active_chats.add(chat_id)

    async def leave_vc(self, chat_id: int):
        self.active_chats.discard(chat_id)


_assistants: list[Assistant] = []
_chat_assistant: dict[int, int] = {}  # chat_id → assistant index


async def init_assistants():
    for i, session in enumerate(Config.STRING_SESSIONS):
        asst = Assistant(session, i)
        await asst.start()
        _assistants.append(asst)
    LOGGER.info(f"{len(_assistants)} assistant(s) loaded.")


async def get_assistant(chat_id: int) -> Optional[Assistant]:
    # Return existing assistant for this chat
    if chat_id in _chat_assistant:
        idx = _chat_assistant[chat_id]
        if idx < len(_assistants):
            return _assistants[idx]

    # Find least busy assistant
    if not _assistants:
        return None
    chosen = min(_assistants, key=lambda a: len(a.active_chats))
    _chat_assistant[chat_id] = chosen.index
    return chosen


def free_assistant(chat_id: int):
    _chat_assistant.pop(chat_id, None)


# ── VC State ──────────────────────────────────────────────────────────────────

_vc_state: dict[int, dict] = {}
_inactivity_tasks: dict[int, asyncio.Task] = {}

# Group settings cache: {chat_id: {effect, volume, speed, bass, mid, treble}}
_group_fx: dict[int, dict] = {}


def get_fx(chat_id: int) -> dict:
    return _group_fx.setdefault(chat_id, {
        "effect": "normal",
        "volume": 100,
        "speed": 1.0,
        "bass": 0,
        "mid": 0,
        "treble": 0,
    })


def set_fx(chat_id: int, **kwargs):
    fx = get_fx(chat_id)
    fx.update(kwargs)


def is_active(chat_id: int) -> bool:
    return chat_id in _vc_state


def get_active_chats() -> list[int]:
    return list(_vc_state.keys())


# ── Stream Control ────────────────────────────────────────────────────────────

async def _build_media_stream(track: Track, chat_id: int) -> MediaStream:
    fx = get_fx(chat_id)
    cmd = build_ffmpeg_cmd(
        track.stream_url,
        effect=fx["effect"],
        volume=fx["volume"],
        speed=fx["speed"],
        bass=fx["bass"],
        mid=fx["mid"],
        treble=fx["treble"],
    )
    # When using ffmpeg_parameters, the first argument to MediaStream
    # can be the stream_url if we don't have -i in ffmpeg_parameters,
    # but build_ffmpeg_cmd includes -i.
    # In pytgcalls, if ffmpeg_parameters is used, it appends them to the default command.
    # To have full control, we should ensure we don't double-include -i.

    return MediaStream(
        track.stream_url,
        audio_quality=AudioQuality.ULTRA_HIGH,
        ffmpeg_parameters=" ".join(cmd[cmd.index("-i") + 2 :]),
    )


async def play_track(chat_id: int, track: Track) -> bool:
    """Play a track in the given chat's VC."""
    asst = await get_assistant(chat_id)
    if not asst:
        LOGGER.error("No assistant available!")
        return False

    try:
        media = await _build_media_stream(track, chat_id)

        if chat_id in _vc_state:
            await asst.calls.change_stream(chat_id, media)
        else:
            await asst.calls.join_group_call(chat_id, media)
            await asst.join_vc(chat_id)
            _vc_state[chat_id] = {"track": track, "paused": False}

        _vc_state[chat_id]["track"] = track
        _vc_state[chat_id]["paused"] = False
        _cancel_inactivity(chat_id)
        LOGGER.info(f"[{chat_id}] Playing: {track.title}")
        return True

    except AlreadyJoinedError:
        try:
            await asst.calls.change_stream(chat_id, media)
            _vc_state[chat_id]["track"] = track
            return True
        except Exception as e:
            LOGGER.error(f"Change stream error [{chat_id}]: {e}")
            return False
    except Exception as e:
        LOGGER.error(f"Play error [{chat_id}]: {e}")
        return False


async def pause_vc(chat_id: int) -> bool:
    asst = await get_assistant(chat_id)
    if not asst or chat_id not in _vc_state:
        return False
    try:
        await asst.calls.pause_stream(chat_id)
        _vc_state[chat_id]["paused"] = True
        _schedule_inactivity(chat_id, asst)
        return True
    except Exception as e:
        LOGGER.error(f"Pause error: {e}")
        return False


async def resume_vc(chat_id: int) -> bool:
    asst = await get_assistant(chat_id)
    if not asst or chat_id not in _vc_state:
        return False
    try:
        await asst.calls.resume_stream(chat_id)
        _vc_state[chat_id]["paused"] = False
        _cancel_inactivity(chat_id)
        return True
    except Exception as e:
        LOGGER.error(f"Resume error: {e}")
        return False


async def stop_vc(chat_id: int):
    asst = await get_assistant(chat_id)
    if not asst:
        return
    try:
        await asst.calls.leave_group_call(chat_id)
    except Exception:
        pass
    finally:
        _vc_state.pop(chat_id, None)
        await asst.leave_vc(chat_id)
        free_assistant(chat_id)
        _cancel_inactivity(chat_id)
        LOGGER.info(f"[{chat_id}] Stopped & left VC.")


async def mute_vc(chat_id: int):
    asst = await get_assistant(chat_id)
    if asst:
        try:
            await asst.calls.mute_stream(chat_id)
        except Exception:
            pass


async def unmute_vc(chat_id: int):
    asst = await get_assistant(chat_id)
    if asst:
        try:
            await asst.calls.unmute_stream(chat_id)
        except Exception:
            pass


async def seek_stream(chat_id: int, seconds: int) -> bool:
    """Seek by re-streaming from the given offset."""
    state = _vc_state.get(chat_id)
    if not state:
        return False
    track = state.get("track")
    if not track:
        return False
    asst = await get_assistant(chat_id)
    if not asst:
        return False

    try:
        fx = get_fx(chat_id)
        cmd = build_ffmpeg_cmd(
            track.stream_url,
            effect=fx["effect"],
            volume=fx["volume"],
            speed=fx["speed"],
        )
        # Insert -ss seek before -i
        i_idx = cmd.index("-i")
        cmd.insert(i_idx, str(seconds))
        cmd.insert(i_idx, "-ss")
        media = MediaStream(
            track.stream_url,
            audio_quality=AudioQuality.ULTRA_HIGH,
            ffmpeg_parameters=" ".join(cmd[2:]),
        )
        await asst.calls.change_stream(chat_id, media)
        return True
    except Exception as e:
        LOGGER.error(f"Seek error: {e}")
        return False


async def update_stream_effects(chat_id: int) -> bool:
    """Re-stream current track with updated effects."""
    state = _vc_state.get(chat_id)
    if not state or not state.get("track"):
        return False
    return await play_track(chat_id, state["track"])


# ── Inactivity Auto-Leave ─────────────────────────────────────────────────────

def _schedule_inactivity(chat_id: int, asst: Assistant):
    _cancel_inactivity(chat_id)

    async def _leave_after():
        await asyncio.sleep(Config.AUTO_LEAVE_TIME)
        LOGGER.info(f"[{chat_id}] Inactivity timeout — leaving VC.")
        await stop_vc(chat_id)
        q = get_queue(chat_id)
        await q.clear()

    task = asyncio.create_task(_leave_after())
    _inactivity_tasks[chat_id] = task


def _cancel_inactivity(chat_id: int):
    task = _inactivity_tasks.pop(chat_id, None)
    if task:
        task.cancel()


# ── Stream Ended Callback (registered by call.py) ─────────────────────────────

_stream_end_callbacks: dict[int, list] = {}


def register_stream_end(chat_id: int, callback):
    _stream_end_callbacks.setdefault(chat_id, []).append(callback)


async def on_stream_end(chat_id: int):
    cbs = _stream_end_callbacks.pop(chat_id, [])
    for cb in cbs:
        try:
            await cb(chat_id)
        except Exception as e:
            LOGGER.error(f"Stream end callback error: {e}")
