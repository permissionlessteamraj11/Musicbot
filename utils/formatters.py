import math
import time


def format_duration(seconds: int) -> str:
    if not seconds or seconds <= 0:
        return "LIVE"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def format_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0 B"
    units = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    return f"{size_bytes / p:.2f} {units[i]}"


def time_ago(timestamp: float) -> str:
    diff = time.time() - timestamp
    if diff < 60:
        return f"{int(diff)}s ago"
    if diff < 3600:
        return f"{int(diff // 60)}m ago"
    if diff < 86400:
        return f"{int(diff // 3600)}h ago"
    return f"{int(diff // 86400)}d ago"


def uptime_string(start_time: float) -> str:
    diff = int(time.time() - start_time)
    days = diff // 86400
    hours = (diff % 86400) // 3600
    mins = (diff % 3600) // 60
    secs = diff % 60
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if mins:
        parts.append(f"{mins}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


def progress_bar(current: int, total: int, length: int = 12) -> str:
    if total <= 0:
        return "▬" * length
    filled = int(length * current / total)
    bar = "█" * filled + "▬" * (length - filled)
    pct = int(100 * current / total)
    return f"{bar} {pct}%"


def truncate(text: str, max_len: int = 40) -> str:
    return text if len(text) <= max_len else text[: max_len - 3] + "..."
