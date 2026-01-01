"""
Main Discord bot for GooseBot
"""
import discord
from discord.ext import commands
import asyncio

try:
    from .config import Config
    from .session_manager import SessionManager
    from .goose_client import GooseClient
    from .handlers import MessageHandler, CommandHandler
    from .utils.logger import setup_logger
except ImportError:
    from config import Config
    from session_manager import SessionManager
    from goose_client import GooseClient
    from handlers import MessageHandler, CommandHandler
    from utils.logger import setup_logger

logger = setup_logger(__name__)


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
        self.goose_client = GooseClient()

    async def setup_hook(self):
        """Set up bot when starting"""
        await self.add_cog(CommandHandler(self, self.session_manager, self.goose_client))
        self.message_handler = MessageHandler(self, self.session_manager, self.goose_client)
        logger.info("Bot setup complete")

    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f"Logged in as {self.user}")
        logger.info(f"Connected to {len(self.guilds)} guilds")

        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
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

    bot = GooseBot()

    try:
        logger.info("Starting GooseBot...")
        await bot.start(Config.DISCORD_BOT_TOKEN)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        await bot.close()


def run():
    """Run the bot"""
    asyncio.run(main())
