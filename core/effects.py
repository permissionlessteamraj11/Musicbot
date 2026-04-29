"""
Audio effect filter chains for FFmpeg.
Each effect returns an `af` (audio filter) string.
"""

EFFECTS = {
    "normal":     "",
    "bassboost":  "equalizer=f=40:width_type=o:width=2:g=15,equalizer=f=80:width_type=o:width=2:g=10",
    "nightcore":  "aresample=48000,asetrate=48000*1.25,atempo=1.25/1.25",
    "vaporwave":  "aresample=48000,asetrate=48000*0.8,atempo=0.8/0.8",
    "3d":         "apulsator=hz=0.08",
    "earrape":    "volume=10",
    "reverb":     "aecho=0.8:0.88:60:0.4",
    "lofi":       "lowpass=f=300,equalizer=f=100:width_type=h:width=200:g=10",
    "treble":     "equalizer=f=8000:width_type=o:width=2:g=10",
    "karaoke":    "pan=stereo|c0=c0-c1|c1=c1-c0",
    "flanger":    "flanger",
    "phaser":     "aphaser",
    "chorus":     "chorus=0.6:0.9:55:0.4:0.25:2",
}

EFFECT_NAMES = list(EFFECTS.keys())


def get_ffmpeg_filter(effect: str, bass: int = 0, mid: int = 0, treble: int = 0) -> str:
    """Build complete audio filter string for FFmpeg -af flag."""
    filters = []

    # Base effect
    base = EFFECTS.get(effect, "")
    if base:
        filters.append(base)

    # Custom EQ on top
    if bass:
        filters.append(f"equalizer=f=60:width_type=o:width=2:g={bass}")
    if mid:
        filters.append(f"equalizer=f=1000:width_type=o:width=2:g={mid}")
    if treble:
        filters.append(f"equalizer=f=8000:width_type=o:width=2:g={treble}")

    return ",".join(filters) if filters else ""


def build_ffmpeg_cmd(
    url: str,
    effect: str = "normal",
    volume: int = 100,
    speed: float = 1.0,
    bass: int = 0,
    mid: int = 0,
    treble: int = 0,
) -> list:
    """Build complete FFmpeg command for PyTgCalls piped audio."""
    af_parts = []

    # Effect chain
    ef = get_ffmpeg_filter(effect, bass, mid, treble)
    if ef:
        af_parts.append(ef)

    # Volume
    if volume != 100:
        af_parts.append(f"volume={volume/100:.2f}")

    # Speed (atempo supports 0.5–2.0, chain for wider range)
    if speed != 1.0:
        speed = max(0.5, min(2.0, speed))
        af_parts.append(f"atempo={speed}")

    cmd = [
        "ffmpeg",
        "-y",
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "5",
        "-i", url,
        "-f", "s16le",
        "-ac", "2",
        "-ar", "48000",
        "-vn",
        "-loglevel", "quiet",
    ]

    if af_parts:
        cmd += ["-af", ",".join(af_parts)]

    cmd.append("pipe:1")
    return cmd
