from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import bot
from core.effects import EFFECT_NAMES
from assistant import set_fx, get_fx, update_stream_effects, is_active
from utils.decorators import admin_or_auth
from utils.database import get_group
from strings import get_string


async def _lang(cid):
    g = await get_group(cid); return g.get("lang", "en")


@bot.on_message(filters.command(["effect", "fx"]) & filters.group)
@admin_or_auth
async def effect_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    lang = await _lang(chat_id)

    if len(message.command) < 2:
        # Show effect selection menu
        buttons = []
        row = []
        for i, name in enumerate(EFFECT_NAMES):
            icon = {
                "normal": "🎵", "bassboost": "🔊", "nightcore": "⚡",
                "vaporwave": "🌊", "3d": "🌐", "earrape": "💢",
                "reverb": "🏛", "lofi": "📻", "treble": "🎶",
                "karaoke": "🎤", "flanger": "🎸", "phaser": "🌀", "chorus": "👥"
            }.get(name, "🎵")
            row.append(InlineKeyboardButton(f"{icon} {name.title()}", callback_data=f"fx_{chat_id}_{name}"))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)

        current_fx = get_fx(chat_id)["effect"]
        await message.reply_text(
            f"🎚 **Audio Effects**\nCurrent: **{current_fx.title()}**\n\nChoose an effect:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    effect = message.command[1].lower()
    if effect not in EFFECT_NAMES:
        await message.reply_text(
            f"❌ Unknown effect. Available:\n`{'`, `'.join(EFFECT_NAMES)}`"
        )
        return

    set_fx(chat_id, effect=effect)
    if is_active(chat_id):
        await update_stream_effects(chat_id)
    await message.reply_text(get_string(lang, "effect_applied", effect=effect.title()))


@bot.on_callback_query(filters.regex(r"^fx_(-?\d+)_(\w+)$"))
@admin_or_auth
async def effect_callback(client: Client, query):
    chat_id = int(query.matches[0].group(1))
    effect = query.matches[0].group(2)
    lang = await _lang(chat_id)

    if effect not in EFFECT_NAMES:
        await query.answer("❌ Unknown effect", show_alert=True)
        return

    set_fx(chat_id, effect=effect)
    if is_active(chat_id):
        await update_stream_effects(chat_id)
    await query.answer(f"✅ {effect.title()} applied!")
    await query.message.edit_text(
        get_string(lang, "effect_applied", effect=effect.title())
    )


@bot.on_message(filters.command(["eq"]) & filters.group)
@admin_or_auth
async def eq_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    lang = await _lang(chat_id)
    parts = message.command[1:]
    if len(parts) < 3:
        await message.reply_text("❌ Usage: `/eq <bass -15 to 15> <mid> <treble>`")
        return
    try:
        bass = max(-15, min(15, int(parts[0])))
        mid = max(-15, min(15, int(parts[1])))
        treble = max(-15, min(15, int(parts[2])))
    except ValueError:
        await message.reply_text("❌ Invalid values. Use integers -15 to 15.")
        return
    set_fx(chat_id, bass=bass, mid=mid, treble=treble)
    if is_active(chat_id):
        await update_stream_effects(chat_id)
    await message.reply_text(
        get_string(lang, "eq_set", bass=bass, mid=mid, treble=treble)
    )


@bot.on_message(filters.command(["resetfx", "rfx"]) & filters.group)
@admin_or_auth
async def resetfx_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    lang = await _lang(chat_id)
    set_fx(chat_id, effect="normal", volume=100, speed=1.0, bass=0, mid=0, treble=0)
    if is_active(chat_id):
        await update_stream_effects(chat_id)
    await message.reply_text(get_string(lang, "effect_reset"))


@bot.on_message(filters.command(["quality"]) & filters.group)
@admin_or_auth
async def quality_cmd(client: Client, message: Message):
    QUALITY_MAP = {"low": 64, "medium": 128, "high": 192, "ultra": 320}
    chat_id = message.chat.id
    if len(message.command) < 2:
        await message.reply_text(
            "🎶 **Audio Quality**\nOptions: `low` (64) | `medium` (128) | `high` (192) | `ultra` (320)\n\nUsage: `/quality ultra`"
        )
        return
    level = message.command[1].lower()
    if level not in QUALITY_MAP:
        await message.reply_text(f"❌ Invalid. Choose: {', '.join(QUALITY_MAP)}")
        return
    from utils.database import update_group
    await update_group(chat_id, {"quality": level})
    await message.reply_text(
        f"✅ Audio quality set to **{level.upper()}** ({QUALITY_MAP[level]} kbps)"
    )
