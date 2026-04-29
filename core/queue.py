import asyncio
import random
from collections import deque
from dataclasses import dataclass, field, asdict
from typing import Optional
from utils.logger import LOGGER

QUEUE_MODE_ONCE = "once"
QUEUE_MODE_LOOP = "loop"
QUEUE_MODE_SHUFFLE = "shuffle"


@dataclass
class Track:
    title: str
    url: str
    stream_url: str
    duration: int
    thumbnail: str
    artist: str
    requester_id: int
    requester_name: str
    source: str = "youtube"
    effect: str = "normal"

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Track":
        return Track(**{k: v for k, v in d.items() if k in Track.__dataclass_fields__})


class GroupQueue:
    def __init__(self, chat_id: int):
        self.chat_id = chat_id
        self._queue: list[Track] = []
        self._history: deque[Track] = deque(maxlen=20)
        self._current: Optional[Track] = None
        self._pos: int = 0
        self._mode: str = QUEUE_MODE_ONCE
        self._lock = asyncio.Lock()

    @property
    def current(self) -> Optional[Track]:
        return self._current

    @property
    def size(self) -> int:
        return len(self._queue)

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def is_empty(self) -> bool:
        return len(self._queue) == 0

    def set_mode(self, mode: str):
        if mode in (QUEUE_MODE_ONCE, QUEUE_MODE_LOOP, QUEUE_MODE_SHUFFLE):
            self._mode = mode

    async def add(self, track: Track) -> int:
        async with self._lock:
            self._queue.append(track)
            return len(self._queue)

    async def add_many(self, tracks: list[Track]):
        async with self._lock:
            self._queue.extend(tracks)

    async def get_next(self) -> Optional[Track]:
        async with self._lock:
            if self._current:
                self._history.appendleft(self._current)

            if self._mode == QUEUE_MODE_LOOP and self._current:
                return self._current

            if not self._queue:
                self._current = None
                return None

            if self._mode == QUEUE_MODE_SHUFFLE:
                idx = random.randrange(len(self._queue))
                track = self._queue.pop(idx)
            else:
                track = self._queue.pop(0)

            self._current = track
            return track

    async def get_prev(self) -> Optional[Track]:
        async with self._lock:
            if not self._history:
                return None
            track = self._history.popleft()
            if self._current:
                self._queue.insert(0, self._current)
            self._current = track
            return track

    async def set_current(self, track: Track):
        async with self._lock:
            self._current = track

    async def remove(self, pos: int) -> Optional[Track]:
        async with self._lock:
            if 1 <= pos <= len(self._queue):
                return self._queue.pop(pos - 1)
            return None

    async def move(self, from_pos: int, to_pos: int) -> bool:
        async with self._lock:
            n = len(self._queue)
            if not (1 <= from_pos <= n and 1 <= to_pos <= n):
                return False
            track = self._queue.pop(from_pos - 1)
            self._queue.insert(to_pos - 1, track)
            return True

    async def shuffle(self):
        async with self._lock:
            random.shuffle(self._queue)

    async def clear(self):
        async with self._lock:
            self._queue.clear()
            self._current = None

    def get_list(self) -> list[Track]:
        return list(self._queue)

    def get_history(self) -> list[Track]:
        return list(self._history)

    def to_serializable(self) -> dict:
        return {
            "queue": [t.to_dict() for t in self._queue],
            "current": self._current.to_dict() if self._current else None,
            "mode": self._mode,
        }

    def load_from_dict(self, data: dict):
        self._queue = [Track.from_dict(t) for t in data.get("queue", [])]
        if data.get("current"):
            self._current = Track.from_dict(data["current"])
        self._mode = data.get("mode", QUEUE_MODE_ONCE)


# ── Global Queue Registry ─────────────────────────────────────────────────────

_queues: dict[int, GroupQueue] = {}


def get_queue(chat_id: int) -> GroupQueue:
    if chat_id not in _queues:
        _queues[chat_id] = GroupQueue(chat_id)
    return _queues[chat_id]


def remove_queue(chat_id: int):
    _queues.pop(chat_id, None)


def get_all_queues() -> dict[int, GroupQueue]:
    return dict(_queues)
