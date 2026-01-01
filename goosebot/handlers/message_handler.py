"""
Message handler for processing Discord messages
"""
import discord
from discord.ext import commands
from typing import Optional
import time

try:
    from ..session_manager import SessionManager
    from ..goose_client import GooseClient
    from ..config import Config
    from ..utils.logger import setup_logger
except ImportError:
    from session_manager import SessionManager
    from goose_client import GooseClient
    from config import Config
    from utils.logger import setup_logger

logger = setup_logger(__name__)


class MessageHandler:
    """Handles Discord message events"""

    def __init__(self, bot: commands.Bot, session_manager: SessionManager, goose_client: GooseClient):
        self.bot = bot
        self.session_manager = session_manager
        self.goose_client = goose_client

    async def handle_message(self, message: discord.Message):
        """Process incoming Discord message"""
        # Debug log to verify we are receiving events
        logger.debug(f"Handling message {message.id} from {message.author}: content='{message.content}' (empty={not message.content}), bot={message.author.bot}")

        if message.author.bot or not message.content:
            return

        bot_user = self.bot.user
        if bot_user is None:
            return

        is_mentioned = bot_user in message.mentions
        is_dm = isinstance(message.channel, discord.DMChannel)
        is_reply = False
        if message.reference and message.reference.resolved:
            if isinstance(message.reference.resolved, discord.Message):
                if message.reference.resolved.author.id == bot_user.id:
                    is_reply = True

        should_reply = is_mentioned or is_dm or is_reply
        
        # Check listening window if not explicitly triggered
        guild_id = message.guild.id if message.guild else 0
        channel_id = message.channel.id
        
        session_info = await self.session_manager.get_session(channel_id)

        if not should_reply and session_info:
            now = time.time()
            delta = now - session_info.last_bot_activity
            is_active = delta < Config.LISTEN_WINDOW_SECONDS
            logger.debug(f"Listening window check: now={now}, last={session_info.last_bot_activity}, delta={delta:.1f}, window={Config.LISTEN_WINDOW_SECONDS} -> active={is_active}")
            
            if is_active:
                should_reply = True

        if not should_reply:
            logger.debug("Ignoring message: not mentioned, not DM, not reply, and listening window expired or no session")
            return

        try:
            await message.channel.typing()

            content = message.content.replace(f"<@{bot_user.id}>", "").replace(f"<@!{bot_user.id}>", "").strip()

            if not content:
                await message.reply("Hi! I'm listening. What would you like me to help you with?")
                return

            if session_info is None:
                session_info = await self.session_manager.create_session(guild_id, channel_id)
                logger.info(f"Created new session info for channel {channel_id}: {session_info.session_name}")

            logger.info(
                f"Processing message from {message.author} in {channel_id}: {content[:50]}..."
            )
            
            # Update activity timestamp immediately when processing starts to extend window
            await self.session_manager.update_activity(channel_id)

            response_message: Optional[discord.Message] = None
            full_response_text = ""
            last_update_time = 0.0

            async def chunk_callback(chunk_text: str):
                """Callback for streaming response chunks to Discord"""
                nonlocal response_message, full_response_text, last_update_time
                
                full_response_text += chunk_text
                current_time = time.time()
                
                if response_message is None:
                    if full_response_text:
                        response_message = await message.reply(full_response_text, mention_author=False)
                        last_update_time = current_time
                        logger.debug(f"Sent initial response chunk: {len(full_response_text)} chars")
                else:
                    # Throttle updates to avoid rate limits (approx 1 per second)
                    if current_time - last_update_time >= 1.0:
                        await response_message.edit(content=full_response_text)
                        last_update_time = current_time
                        logger.debug(f"Updated response chunk: {len(full_response_text)} chars")

            response = await self.goose_client.send_message(
                session_name=session_info.session_name,
                message=content,
                resume=True,
                chunk_callback=chunk_callback,
            )

            # Update activity again after response is complete
            await self.session_manager.update_activity(channel_id)

            # Ensure final state matches accumulated text
            if response_message and full_response_text:
                await response_message.edit(content=full_response_text)

            if "No session found" in response:
                logger.warning(f"Session not found, creating and retrying: {session_info.session_name}")
                response = await self.goose_client.send_message(
                    session_name=session_info.session_name,
                    message=content,
                    resume=False,
                    chunk_callback=chunk_callback,
                )
                logger.info(f"Sent message without resume flag to create session")

            await self.session_manager.increment_message_count(channel_id)

            if response and not response_message:
                await message.reply(response, mention_author=False)
            elif not response and not response_message:
                await message.reply("No response from Goose", mention_author=False)

        except discord.Forbidden:
            logger.error(f"No permission to reply in channel {message.channel.id}")
        except discord.HTTPException as e:
            logger.error(f"Discord API error: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            try:
                await message.reply(f"❌ Error processing message: {str(e)}", mention_author=False)
            except:
                pass
