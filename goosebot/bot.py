"""
Main Discord bot for GooseBot
"""
import discord
from discord.ext import commands
import asyncio
import time
import logging
from pathlib import Path

try:
    from .config import Config
    from .session_manager import SessionManager
    from .goose_client import GooseClient
    from .handlers import MessageHandler, CommandHandler
    from .utils.logger import setup_logger
    from .tui import GooseTUI, RequestUpdateEvent, LogEvent, BotStatusEvent, RequestStatus
    from .tui.logger_handler import TUILogHandler
except ImportError:
    from config import Config
    from session_manager import SessionManager
    from goose_client import GooseClient
    from handlers import MessageHandler, CommandHandler
    from utils.logger import setup_logger
    from tui import GooseTUI, RequestUpdateEvent, LogEvent, BotStatusEvent, RequestStatus
    from tui.logger_handler import TUILogHandler

tui_event_queue = asyncio.Queue()
log_path = Path("goosebot.log")
logger = setup_logger(
    __name__, 
    log_file=log_path,
    disable_console=True, 
    extra_handlers=[TUILogHandler(tui_event_queue)]
)


class GooseBot(commands.Bot):
    """Discord bot for Goose.ai integration"""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True
        intents.guilds = True
        intents.members = True

        super().__init__(
            command_prefix=Config.BOT_PREFIX,
            intents=intents,
            help_command=None,
        )

        self.session_manager = SessionManager()
        self.goose_client = GooseClient(model=Config.GOOSE_MODEL)
        self.tui_queue = tui_event_queue

    async def setup_hook(self):
        """Set up bot when starting"""
        await self.add_cog(CommandHandler(self, self.session_manager, self.goose_client, self.tui_queue))
        self.message_handler = MessageHandler(self, self.session_manager, self.goose_client, self.tui_queue)
        logger.info("Bot setup complete")

    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f"Logged in as {self.user}")
        logger.info(f"Connected to {len(self.guilds)} guilds")

        try:
            # Sync to each guild for immediate availability
            for guild in self.guilds:
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
            
            # Also sync globally
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s) globally and to {len(self.guilds)} guilds")
            
            # Send initial status to TUI
            await self.tui_queue.put(BotStatusEvent(
                timestamp=time.time(),
                is_connected=True,
                guild_count=len(self.guilds),
                user_name=str(self.user)
            ))
        except Exception as e:
            logger.error(f"Error syncing commands: {e}", exc_info=True)

    async def on_message(self, message: discord.Message):
        """Handle incoming messages"""
        if message.author == self.user:
            return

        await self.message_handler.handle_message(message)

        await self.process_commands(message)

    async def close(self):
        """Clean shutdown"""
        logger.info("Shutting down bot...")
        await self.goose_client.stop()
        await super().close()


async def main():
    """Main entry point"""
    is_valid, msg = Config.validate()
    if not is_valid:
        logger.error(f"Configuration error: {msg}")
        print(f"❌ {msg}")
        return

    # Silence external loggers that might output to console
    logging.getLogger("discord").propagate = False
    logging.getLogger("textual").propagate = False
    setup_logger("discord", log_file=log_path, level=logging.INFO)
    setup_logger("textual", log_file=log_path, level=logging.INFO)

    bot = GooseBot()
    tui = GooseTUI(tui_event_queue)

    try:
        logger.info("Starting GooseBot...")
        # Start bot as a background task
        bot_task = asyncio.create_task(bot.start(Config.DISCORD_BOT_TOKEN))
        
        # Give TUI a moment to start before sending first status if already connected
        async def delayed_status():
            await asyncio.sleep(2)
            if bot.is_ready():
                 await tui_event_queue.put(BotStatusEvent(
                    timestamp=time.time(),
                    is_connected=True,
                    guild_count=len(bot.guilds),
                    user_name=str(bot.user)
                ))
        
        asyncio.create_task(delayed_status())

        # Run TUI in the main task
        await tui.run_async()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        await bot.close()
        # Ensure bot task is cleaned up
        if 'bot_task' in locals():
            bot_task.cancel()
            try:
                await bot_task
            except asyncio.CancelledError:
                pass


def run():
    """Run the bot"""
    asyncio.run(main())
