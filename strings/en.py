STRINGS = {
    # ── General ────────────────────────────────────────────
    "start_text": (
        "**{bot_name}**\n\n"
        "A high-performance, professional-grade Telegram Voice Chat music system.\n\n"
        "**System Statistics**\n"
        "├ Groups: `{groups}`\n"
        "├ Users: `{users}`\n"
        "├ Total Streams: `{plays}`\n"
        "└ System Uptime: `{uptime}`\n\n"
        "Select **Add to Group** to initialize."
    ),
    "help_text": (
        "**{bot_name} — Command Interface**\n\n"
        "**Playback Control**\n"
        "`/play` — Stream from YouTube or Spotify\n"
        "`/vplay` — Initialize video stream in Voice Chat\n"
        "`/fplay` — Stream local media file\n"
        "`/livestream` — Access external live stream\n"
        "`/radio` — Global radio access\n"
        "`/playlist` — Batch queue processing\n\n"
        "**Active Controls**\n"
        "`/pause` | `/resume` | `/skip` | `/back`\n"
        "`/seek` | `/rewind` | `/loop` | `/shuffle`\n"
        "`/volume` | `/speed` | `/mute` | `/unmute`\n\n"
        "**Queue Management**\n"
        "`/queue` | `/remove` | `/move` | `/clearqueue`\n\n"
        "**Audio Processing**\n"
        "`/effect` | `/eq` | `/resetfx`\n\n"
        "**Information**\n"
        "`/song` | `/lyrics` | `/history` | `/suggest`\n\n"
        "**Administration**\n"
        "`/lock` | `/unlock` | `/auth` | `/setlimit`\n"
    ),
    "no_active_call": "Error: No active voice call detected in this group.",
    "not_in_vc": "System Status: Not currently connected to a voice chat.",
    "already_paused": "Status: Stream is already paused.",
    "already_playing": "Status: Stream is already active.",
    "queue_empty": "Information: The queue is currently empty.",
    "invalid_args": "Error: Invalid parameters provided. Proper usage: `{usage}`",
    "banned": "Access Denied: You have been restricted from using this system.",
    "rate_limited": "System Alert: Request limit exceeded. Maximum {limit} requests per minute.",
    "maintenance": "System Alert: Maintenance in progress. Services will resume shortly.",
    "only_admin": "Access Denied: Administrative privileges required.",
    "only_owner": "Access Denied: System owner privileges required.",
    "locked": "Access Denied: System is currently locked to administrative use only.",
    # ── Play ───────────────────────────────────────────────
    "searching": "Processing query: `{query}`...",
    "downloading": "Retrieving data...",
    "playing_now": "Currently Streaming",
    "added_to_queue": "**Track Queued** [Position #{pos}]\n\nTitle: {title}\nDuration: {duration}",
    "queue_full": "Error: Queue capacity reached. Maximum allowed: {max} tracks.",
    "song_blacklisted": "Access Denied: This content has been restricted in this group.",
    "duration_too_long": "Error: Content exceeds maximum duration. Limit: {max}.",
    "no_results": "Error: No results found for query: `{query}`.",
    "live_stream": "Active Live Stream: **{title}**",
    # ── Controls ───────────────────────────────────────────
    "paused": "**Stream Paused**",
    "resumed": "**Stream Resumed**",
    "skipped": "**Track Skipped** — Initializing next track in queue.",
    "skipped_all": "**Stream Terminated** — All queue data cleared.",
    "replaying": "**Restarting Track** — Re-initializing current stream.",
    "looping_on": "**Loop Enabled** for current track.",
    "looping_off": "**Loop Disabled**",
    "shuffled": "**Queue Shuffled** — Track sequence randomized.",
    "volume_set": "Audio Level adjusted to **{vol}%**",
    "speed_set": "Playback Speed adjusted to **{speed}x**",
    "muted": "**Audio Muted**",
    "unmuted": "**Audio Unmuted**",
    "seeked": "Stream offset adjusted to `{time}`",
    "nothing_playing": "Error: No active stream detected.",
    # ── Queue ──────────────────────────────────────────────
    "queue_header": "**System Queue** — {count} active track(s)\n\n",
    "queue_item": "{pos}. {title} [{duration}] — Requested by: {req}\n",
    "queue_now": "**Active Stream:** {title} [{duration}]\n\n",
    # ── Admin ──────────────────────────────────────────────
    "locked_msg": "Administrative Lock: System restricted to admins.",
    "unlocked_msg": "Administrative Unlock: System accessible to all users.",
    "authed": "Authorization Granted: {user} now has access to restricted commands.",
    "unauthed": "Authorization Revoked: {user} no longer has access to restricted commands.",
    "limit_set": "Configuration Updated: Queue limit set to **{n}** tracks per user.",
    "log_set": "Configuration Updated: Log channel assigned to {ch}.",
    "prefix_set": "Configuration Updated: Command prefix changed to `{prefix}`.",
    "blacklisted_song": "Configuration Updated: Track added to system blacklist.",
    # ── Effects ────────────────────────────────────────────
    "effect_applied": "Audio Processing: **{effect}** profile applied.",
    "effect_reset": "Audio Processing: All filters have been reset.",
    "eq_set": "Equalizer Updated — Bass: {bass} | Mid: {mid} | Treble: {treble}",
    # ── Stats / Info ───────────────────────────────────────
    "stats_text": (
        "**System Statistics**\n\n"
        "├ Groups: `{groups}`\n"
        "├ Users: `{users}`\n"
        "├ Total Streams: `{plays}`\n"
        "├ Active Voice Chats: `{active_vc}`\n"
        "└ System Uptime: `{uptime}`\n"
    ),
    "vote_skip": "**Skip Vote Initialized** — Current: {votes}/{needed} votes required.\nSelect below to cast your vote.",
    "vote_skip_done": "Success: Skip vote passed. Executing skip...",
    # ── Clone ──────────────────────────────────────────────
    "clone_text": (
        "**System Replication**\n\n"
        "Deploy a dedicated instance of this system.\n\n"
        "1. Obtain API credentials from my.telegram.org\n"
        "2. Register a bot via @BotFather\n"
        "3. Configure environmental variables\n"
        "4. Initialize deployment on high-availability server\n"
    ),
    "no_active_vc": "Information: No active voice chats detected.",
}
