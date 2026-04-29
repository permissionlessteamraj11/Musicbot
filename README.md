# 🎵 MusicBot — Production-Grade Telegram VC Music Bot

A blazing-fast, feature-rich Telegram Voice Chat music bot with
320kbps audio, Spotify integration, clone system, and much more.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🔊 Audio Quality | Up to 320kbps stereo, 48kHz |
| 🎚 Audio Effects | Bass Boost, Nightcore, Vaporwave, 3D, Reverb, Lofi & more |
| 📻 Sources | YouTube, Spotify (tracks/playlists/albums), Radio |
| 🤖 Clone System | Full self-clone with VPS/Heroku deploy guides |
| 👥 Multi-Assistant | Up to 5 Pyrogram accounts, auto load-balanced |
| 📋 Queue System | Per-group queue with Loop/Shuffle/Once modes |
| 🎨 Now Playing Card | Dynamic Pillow-generated card with album art |
| 🌐 Web Panel | FastAPI admin dashboard at port 8080 |
| 💾 Persistence | MongoDB + Redis — queue survives restart |
| 🇮🇳 Multilingual | English + Hindi support per group |

---

## 🚀 Quick Deploy (VPS)

### Prerequisites
- Ubuntu 22.04 VPS (1GB RAM minimum)
- Python 3.11+
- FFmpeg installed
- MongoDB & Redis running

### Steps

```bash
# 1. Install system deps
apt update && apt install -y ffmpeg python3.11 python3-pip python3-venv redis-server mongodb git curl
npm i -g pm2

# 2. Clone repo
git clone https://github.com/yourrepo/musicbot
cd musicbot

# 3. Setup virtual environment
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 4. Download fonts
mkdir -p assets/fonts cache/thumbnails logs
curl -sL "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf" -o assets/fonts/Poppins-Bold.ttf
curl -sL "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf" -o assets/fonts/Poppins-Regular.ttf

# 5. Configure
cp .env.example .env
nano .env   # Fill in your values

# 6. Generate String Session
python3 -c "from pyrogram import Client; Client('session', api_id=YOUR_API_ID, api_hash='YOUR_API_HASH').run()"

# 7. Start
pm2 start "python3 -m musicbot" --name MusicBot
pm2 save && pm2 startup
```

---

## 🐳 Docker Deploy

```bash
cp .env.example .env
# Edit .env with your values
nano .env

docker-compose up -d
```

---

## ⚙️ Configuration

| Variable | Description |
|---|---|
| `API_ID` | Telegram API ID from my.telegram.org |
| `API_HASH` | Telegram API Hash |
| `BOT_TOKEN` | Bot token from @BotFather |
| `STRING_SESSION` | Pyrogram string session (comma-sep for multiple) |
| `OWNER_ID` | Your Telegram user ID |
| `MONGO_URI` | MongoDB connection string |
| `REDIS_URL` | Redis connection URL |
| `SPOTIFY_CLIENT_ID` | Spotify app client ID |
| `SPOTIFY_CLIENT_SECRET` | Spotify app client secret |
| `GENIUS_API_TOKEN` | Genius API token for lyrics |
| `BOT_NAME` | Custom bot display name |
| `MAX_QUEUE_SIZE` | Max songs in queue (default: 100) |
| `AUTO_LEAVE_TIME` | Inactivity timeout in seconds (default: 300) |

---

## 📋 Commands

### Playback
| Command | Description |
|---|---|
| `/play <query/url>` | Play from YouTube/Spotify |
| `/vplay <query>` | Play video in VC |
| `/fplay` | Play uploaded audio file |
| `/livestream <url>` | Stream live URL |
| `/radio <station>` | Play internet radio |
| `/playlist <url>` | Queue full playlist |
| `/search <query>` | Search and pick from results |

### Controls
| Command | Description |
|---|---|
| `/pause` `/resume` | Pause/Resume |
| `/skip` `/back` | Skip/Previous track |
| `/loop` | Toggle loop |
| `/shuffle` | Shuffle queue |
| `/volume 1-200` | Set volume |
| `/speed 0.5-2.0` | Playback speed |
| `/seek <seconds>` | Jump to timestamp |
| `/247` | Toggle 24/7 mode |
| `/sleep <mins>` | Sleep timer |

### Audio Effects
| Command | Description |
|---|---|
| `/effect <name>` | Apply audio effect |
| `/eq <bass> <mid> <treble>` | Custom EQ |
| `/quality low\|medium\|high\|ultra` | Audio quality |
| `/resetfx` | Reset all effects |

**Available Effects:** normal, bassboost, nightcore, vaporwave, 3d, earrape, reverb, lofi, treble, karaoke, flanger, phaser, chorus

### Queue
`/queue` `/remove <pos>` `/move <from> <to>` `/clearqueue` `/queuetype loop|once|shuffle`

### Admin (Group Admins)
`/lock` `/unlock` `/auth` `/unauth` `/setlimit` `/setlog` `/setlang en|hi` `/blacklist` `/topreq` `/topsongs`

### Owner/Sudo
`/stats` `/broadcast` `/gban` `/addsudo` `/restart` `/update` `/maintenance` `/activevc` `/clone` `/clones`

---

## 🤖 Clone System

Send `/clone` to the bot in PM to get full deployment instructions with one-click buttons.

---

## 🌐 Web Dashboard

Access at `http://your-vps-ip:8080` after starting the bot.
Shows real-time stats: groups, users, plays, CPU, RAM, active VCs.

---

## 📂 Project Structure

```
musicbot/
├── __main__.py         # Entry point
├── bot.py              # Pyrogram client
├── assistant.py        # PyTgCalls assistant pool
├── config.py           # Configuration
├── core/
│   ├── call.py         # Stream lifecycle
│   ├── queue.py        # Per-group queue
│   ├── downloader.py   # yt-dlp + Spotify
│   └── effects.py      # FFmpeg audio filters
├── plugins/
│   ├── play.py         # Playback commands
│   ├── controls.py     # Player controls
│   ├── queue.py        # Queue management
│   ├── effects.py      # Audio effects
│   ├── admin.py        # Group admin
│   ├── sudo.py         # Owner/sudo
│   ├── lyrics.py       # Lyrics + suggestions
│   ├── clone.py        # Clone system
│   └── start.py        # Start/Help/Inline
├── utils/
│   ├── database.py     # MongoDB helpers
│   ├── cache.py        # Redis helpers
│   ├── thumbnail.py    # Now Playing card
│   ├── formatters.py   # Utilities
│   ├── decorators.py   # Auth decorators
│   └── logger.py       # Logging
├── web/
│   ├── app.py          # FastAPI panel
│   └── templates/
│       └── dashboard.html
├── strings/
│   ├── en.py
│   └── hi.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## 📄 License

MIT License — Free to use, modify, and deploy.
