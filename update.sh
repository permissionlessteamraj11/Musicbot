#!/bin/bash
# ── MusicBot Auto-Update Script ──────────────────────
set -e
echo "⬇️  Pulling latest code..."
git pull origin main

echo "📦 Installing/updating dependencies..."
source venv/bin/activate
pip install -r requirements.txt -q

echo "🔄 Restarting bot with PM2..."
pm2 restart MusicBot

echo "✅ Update complete!"
pm2 logs MusicBot --lines 20
