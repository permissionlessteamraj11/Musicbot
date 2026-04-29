import asyncio
import signal
import sys
from utils.logger import LOGGER


async def main():
    LOGGER.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    LOGGER.info("   🎵  MusicBot  —  Starting Up")
    LOGGER.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # Validate config
    from config import Config
    if not Config.API_ID or not Config.API_HASH or not Config.BOT_TOKEN:
        LOGGER.critical("API_ID, API_HASH, or BOT_TOKEN is missing! Check your .env file.")
        sys.exit(1)
    if not Config.STRING_SESSIONS:
        LOGGER.critical("No STRING_SESSION found! Bot cannot stream audio without it.")
        sys.exit(1)

    # Init database connections
    from utils.database import get_db
    await get_db()
    from utils.cache import get_redis
    await get_redis()

    # Load assistants (PyTgCalls user accounts)
    from assistant import init_assistants
    await init_assistants()

    # Register PyTgCalls stream-end callback
    await _register_stream_callbacks()

    # Start bot
    from bot import bot
    await bot.start()
    me = await bot.get_me()
    LOGGER.info(f"Bot started: @{me.username} ({me.id})")

    # Start web panel
    from web.app import start_web
    web_task = asyncio.create_task(start_web())
    LOGGER.info("Web panel running at http://0.0.0.0:8080")

    # Start clone heartbeat
    from plugins.clone import start_heartbeat
    asyncio.create_task(start_heartbeat())

    # Check for restart recovery
    await _check_restart_recovery(bot)

    LOGGER.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    LOGGER.info("   ✅  Bot is LIVE and ready!")
    LOGGER.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # Graceful shutdown handler
    def _handle_shutdown(sig, frame):
        LOGGER.info("Shutdown signal received...")
        asyncio.create_task(_shutdown(bot))

    signal.signal(signal.SIGTERM, _handle_shutdown)
    signal.signal(signal.SIGINT, _handle_shutdown)

    await asyncio.Event().wait()  # Run forever


async def _register_stream_callbacks():
    """Wire PyTgCalls stream-end events to our play_next handler."""
    from assistant import _assistants
    from core.call import handle_stream_end
    from bot import bot

    for asst in _assistants:
        @asst.calls.on_stream_end()
        async def _on_end(_, update):
            try:
                chat_id = update.chat_id
                await handle_stream_end(bot, chat_id)
            except Exception as e:
                from utils.logger import LOGGER
                LOGGER.error(f"Stream end handler error: {e}")


async def _check_restart_recovery(bot):
    """After restart, send confirmation message if triggered by /restart."""
    from utils.cache import get_key, del_key
    chat_id = await get_key("restart_chat")
    msg_id = await get_key("restart_msg")
    if chat_id:
        try:
            from utils.formatters import uptime_string
            from bot import START_TIME
            await bot.send_message(
                int(chat_id),
                "✅ **Bot restarted successfully!**\n"
                f"⏱ Uptime: `{uptime_string(START_TIME)}`",
            )
        except Exception:
            pass
        await del_key("restart_chat")
        await del_key("restart_msg")


async def _shutdown(bot):
    """Graceful shutdown — save queue states then stop."""
    LOGGER.info("Saving queue states before shutdown...")
    from core.queue import get_all_queues
    from utils.database import save_queue

    for chat_id, q in get_all_queues().items():
        try:
            data = q.to_serializable()
            await save_queue(chat_id, data["queue"], 0)
        except Exception:
            pass

    # Leave all VCs
    from assistant import _assistants, get_active_chats, stop_vc
    for chat_id in list(get_active_chats()):
        try:
            await stop_vc(chat_id)
        except Exception:
            pass

    await bot.stop()
    LOGGER.info("Bot stopped gracefully. Goodbye!")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
