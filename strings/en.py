STRINGS = {
    # ── General ────────────────────────────────────────────
    "start_text": (
        "🎵 **{bot_name}**\n\n"
        "A blazing-fast, high-quality Telegram Voice Chat music bot.\n\n"
        "📊 **Stats**\n"
        "├ Groups: `{groups}`\n"
        "├ Users: `{users}`\n"
        "├ Total Plays: `{plays}`\n"
        "└ Uptime: `{uptime}`\n\n"
        "Tap **Add to Group** to get started!"
    ),
    "help_text": (
        "🎵 **{bot_name} — Commands**\n\n"
        "**Playback**\n"
        "`/play` — Play song/URL\n"
        "`/vplay` — Play video in VC\n"
        "`/fplay` — Play uploaded file\n"
        "`/livestream` — Stream live URL\n"
        "`/radio` — Internet radio\n"
        "`/playlist` — Queue full playlist\n\n"
        "**Controls**\n"
        "`/pause` `/resume` `/skip` `/back`\n"
        "`/seek` `/rewind` `/loop` `/shuffle`\n"
        "`/volume` `/speed` `/mute` `/unmute`\n\n"
        "**Queue**\n"
        "`/queue` `/remove` `/move` `/clearqueue`\n\n"
        "**Effects**\n"
        "`/effect` `/eq` `/resetfx`\n\n"
        "**Info**\n"
        "`/song` `/lyrics` `/history` `/suggest`\n\n"
        "**Admin**\n"
        "`/lock` `/unlock` `/auth` `/setlimit`\n"
    ),
    "no_active_call": "❌ No active voice call in this group.",
    "not_in_vc": "❌ I'm not in a voice chat right now.",
    "already_paused": "⏸ Already paused.",
    "already_playing": "▶️ Already playing.",
    "queue_empty": "📭 Queue is empty.",
    "invalid_args": "❌ Invalid arguments. Usage: `{usage}`",
    "banned": "🚫 You are globally banned from this bot.",
    "rate_limited": "⚠️ Slow down! Max {limit} plays per minute.",
    "maintenance": "🔧 Bot is under maintenance. Please wait.",
    "only_admin": "❌ Only group admins can use this.",
    "only_owner": "❌ Only bot owner can use this.",
    "locked": "🔒 Bot is locked. Only admins can use commands.",
    # ── Play ───────────────────────────────────────────────
    "searching": "🔍 Searching for `{query}`...",
    "downloading": "⬇️ Downloading...",
    "playing_now": "🎵 Now Playing",
    "added_to_queue": "➕ **Added to Queue** [#{pos}]\n\n🎵 {title}\n⏱ {duration}",
    "queue_full": "❌ Queue is full! Max {max} songs.",
    "song_blacklisted": "🚫 This song is blacklisted in this group.",
    "duration_too_long": "❌ Song too long! Max allowed: {max}.",
    "no_results": "❌ No results found for `{query}`.",
    "live_stream": "📡 Streaming live: **{title}**",
    # ── Controls ───────────────────────────────────────────
    "paused": "⏸ **Paused**",
    "resumed": "▶️ **Resumed**",
    "skipped": "⏭ **Skipped** → Now playing next track",
    "skipped_all": "⏹ **Stopped** — Queue cleared.",
    "replaying": "🔄 **Replaying** current track",
    "looping_on": "🔁 **Loop ON** for current track",
    "looping_off": "➡️ **Loop OFF**",
    "shuffled": "🔀 **Queue shuffled!**",
    "volume_set": "🔊 Volume set to **{vol}%**",
    "speed_set": "⚡ Speed set to **{speed}x**",
    "muted": "🔇 **Muted**",
    "unmuted": "🔊 **Unmuted**",
    "seeked": "⏩ Seeked to `{time}`",
    "nothing_playing": "❌ Nothing is playing right now.",
    # ── Queue ──────────────────────────────────────────────
    "queue_header": "📋 **Queue** — {count} track(s)\n\n",
    "queue_item": "{pos}. {title} [{duration}] — by {req}\n",
    "queue_now": "▶️ **Now:** {title} [{duration}]\n\n",
    # ── Admin ──────────────────────────────────────────────
    "locked_msg": "🔒 Bot **locked**. Only admins can use commands.",
    "unlocked_msg": "🔓 Bot **unlocked**. Everyone can use commands.",
    "authed": "✅ {user} is now authorized.",
    "unauthed": "❌ {user} is no longer authorized.",
    "limit_set": "✅ Queue limit set to **{n}** songs per user.",
    "log_set": "✅ Log channel set to {ch}.",
    "prefix_set": "✅ Command prefix changed to `{prefix}`.",
    "blacklisted_song": "✅ Song added to blacklist.",
    # ── Effects ────────────────────────────────────────────
    "effect_applied": "🎚 Effect **{effect}** applied!",
    "effect_reset": "✅ All audio effects reset.",
    "eq_set": "🎛 EQ set — Bass: {bass} | Mid: {mid} | Treble: {treble}",
    # ── Stats / Info ───────────────────────────────────────
    "stats_text": (
        "📊 **Bot Statistics**\n\n"
        "├ Groups: `{groups}`\n"
        "├ Users: `{users}`\n"
        "├ Total Plays: `{plays}`\n"
        "├ Active VCs: `{active_vc}`\n"
        "└ Uptime: `{uptime}`\n"
    ),
    "vote_skip": "🗳 **Vote Skip** — {votes}/{needed} votes\nTap below to vote!",
    "vote_skip_done": "✅ Vote skip passed! Skipping...",
    # ── Clone ──────────────────────────────────────────────
    "clone_text": (
        "🤖 **Clone {bot_name}**\n\n"
        "Deploy your own instance of this bot!\n\n"
        "1. Get API credentials from my.telegram.org\n"
        "2. Create a bot via @BotFather\n"
        "3. Fill in the config below\n"
        "4. Deploy on your VPS\n"
    ),
    "no_active_vc": "ℹ️ No active voice chats right now.",
}
