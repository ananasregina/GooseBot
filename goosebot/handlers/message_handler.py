"""
Message handler for processing Discord messages
"""
import discord
from discord.ext import commands
from typing import Optional
import time
import asyncio
import base64

try:
    from ..session_manager import SessionManager
    from ..goose_client import GooseClient
    from ..config import Config
    from ..utils.logger import setup_logger
    from ..tui import RequestUpdateEvent, RequestStatus
    from ..utils.context import get_context_instructions
except ImportError:
    from session_manager import SessionManager
    from goose_client import GooseClient
    from config import Config
    from utils.logger import setup_logger
    from tui import RequestUpdateEvent, RequestStatus
    from utils.context import get_context_instructions

logger = setup_logger(__name__)


class MessageHandler:
    """Handles Discord message events"""

    def __init__(self, bot: commands.Bot, session_manager: SessionManager, goose_client: GooseClient, tui_queue: Optional[asyncio.Queue] = None):
        self.bot = bot
        self.session_manager = session_manager
        self.goose_client = goose_client
        self.tui_queue = tui_queue

    async def _emit_event(self, event: RequestUpdateEvent):
        if self.tui_queue:
            await self.tui_queue.put(event)

    async def handle_message(self, message: discord.Message):
        """Process incoming Discord message"""
        # Debug log to verify we are receiving events
        logger.debug(f"Handling message {message.id} from {message.author}: content='{message.content}' (empty={not message.content}), bot={message.author.bot}")

        if message.author.bot:
            return
        
        # Allow empty content if there are attachments
        if not message.content and not message.attachments:
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

        # Emit initial event
        request_id = str(message.id)
        await self._emit_event(RequestUpdateEvent(
            timestamp=time.time(),
            request_id=request_id,
            status=RequestStatus.RECEIVED,
            user=str(message.author),
            channel=str(message.channel),
            message_content=message.clean_content
        ))

        try:
            async with message.channel.typing():
                # Use clean_content to resolve mentions to names, then strip bot name if still present
                content = message.clean_content.replace(f"@{bot_user.display_name}", "").replace(f"@{bot_user.name}", "").strip()
                
                # If bot_user is in simple @Bot format in clean_content
                if content.startswith(bot_user.display_name):
                    content = content[len(bot_user.display_name):].strip()

                if not content:
                    await message.reply("Hi! I'm listening. What would you like me to help you with?")
                    return

                if session_info is None:
                    session_info = await self.session_manager.create_session(guild_id, channel_id)
                    logger.info(f"Created new session info for channel {channel_id}: {session_info.session_name}")

                logger.info(
                    f"Processing message from {message.author} in {channel_id}: {content[:50]}..."
                )
                
                # Update status to QUEUING/PROCESSING
                await self._emit_event(RequestUpdateEvent(
                    timestamp=time.time(),
                    request_id=request_id,
                    status=RequestStatus.PROCESSING,
                    user=str(message.author),
                    channel=str(message.channel),
                    message_content=message.clean_content,
                    progress=0.1
                ))

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
                            
                            # Update status to RESPONDING
                            await self._emit_event(RequestUpdateEvent(
                                timestamp=current_time,
                                request_id=request_id,
                                status=RequestStatus.RESPONDING,
                                user=str(message.author),
                                channel=str(message.channel),
                                message_content=message.content,
                                progress=0.5
                            ))
                    else:
                        # Throttle updates to avoid rate limits (approx 1 per second)
                        # CRITICAL: We only throttle if there's enough time left. 
                        # The final update is handled after send_message returns.
                        if current_time - last_update_time >= 1.0:
                            try:
                                await response_message.edit(content=full_response_text)
                                last_update_time = current_time
                                logger.debug(f"Updated response chunk: {len(full_response_text)} chars")
                                
                                # Update progress slightly
                                await self._emit_event(RequestUpdateEvent(
                                    timestamp=current_time,
                                    request_id=request_id,
                                    status=RequestStatus.RESPONDING,
                                    user=str(message.author),
                                    channel=str(message.channel),
                                    message_content=message.content,
                                    progress=min(0.9, 0.5 + (len(full_response_text) / 2000)) # Fake progress
                                ))
                            except discord.HTTPException as e:
                                logger.warning(f"Failed to update chunk: {e}")

                # Construct instructions for new sessions
                instructions = get_context_instructions(
                    message.author, message.channel, message.guild, bot_user
                )

                # Process attachments
                processed_attachments = []
                if message.attachments:
                    # Check if model supports images
                    capabilities = self.goose_client.capabilities
                    supports_images = capabilities.get("promptCapabilities", {}).get("image", False)
                    
                    for attachment in message.attachments:
                        if attachment.content_type and attachment.content_type.startswith("image/"):
                            if not supports_images:
                                await message.reply(f"⚠️ The current model does not support images. Ignoring attachment: {attachment.filename}")
                                continue
                                
                            try:
                                logger.info(f"Processing image attachment: {attachment.filename} ({attachment.content_type})")
                                image_data = await attachment.read()
                                base64_data = base64.b64encode(image_data).decode('utf-8')
                                processed_attachments.append({
                                    "data": base64_data,
                                    "media_type": attachment.content_type
                                })
                            except Exception as e:
                                logger.error(f"Failed to process attachment {attachment.filename}: {e}")
                                await message.reply(f"❌ Failed to process attachment: {attachment.filename}")
                        else:
                            # Non-image attachments - for now we just warn
                            logger.warning(f"Unsupported attachment type: {attachment.content_type}")
                            await message.reply(f"⚠️ Unsupported attachment type: {attachment.filename}. Currently only images are supported.")

                response = await self.goose_client.send_message(
                    session_name=session_info.session_name,
                    message=content,
                    resume=True,
                    chunk_callback=chunk_callback,
                    instructions=instructions,
                    attachments=processed_attachments if processed_attachments else None,
                )
                
                # Update activity again after response is complete
                await self.session_manager.update_activity(channel_id)

                # If the final response from goose_client contains more content than we captured in chunks,
                # or if we didn't get any chunks at all, update our full_response_text.
                if response and isinstance(response, str) and len(response) > len(full_response_text):
                    logger.debug(f"Final response longer than streamed chunks ({len(response)} vs {len(full_response_text)}). Using final response.")
                    full_response_text = response

                # Ensure final state matches accumulated text - ALWAYS update one last time
                if response_message and full_response_text:
                    try:
                        logger.debug(f"Finalizing message update: {len(full_response_text)} chars")
                        await response_message.edit(content=full_response_text)
                    except discord.HTTPException as e:
                        logger.warning(f"Failed to final update message: {e}")

                if "No session found" in str(response):
                    logger.warning(f"Session not found, creating and retrying: {session_info.session_name}")
                    response = await self.goose_client.send_message(
                        session_name=session_info.session_name,
                        message=content,
                        resume=False,
                        chunk_callback=chunk_callback,
                        instructions=instructions,
                    )
                    logger.info(f"Sent message without resume flag to create session")

                await self.session_manager.increment_message_count(channel_id)

                if not response and not response_message and full_response_text:
                     # This might happen if we had chunks but the final return was suppressed (e.g. tool output)
                     response_message = await message.reply(full_response_text, mention_author=False)

                if response and not response_message:
                    await message.reply(response, mention_author=False)
                elif not response and not response_message and not full_response_text:
                    await message.reply("No response from Goose", mention_author=False)

                # Mark as COMPLETED
                await self._emit_event(RequestUpdateEvent(
                    timestamp=time.time(),
                    request_id=request_id,
                    status=RequestStatus.COMPLETED,
                    user=str(message.author),
                    channel=str(message.channel),
                    message_content=message.content,
                    progress=1.0
                ))

        except discord.Forbidden:
            logger.error(f"No permission to reply in channel {message.channel.id}")
            await self._emit_event(RequestUpdateEvent(
                timestamp=time.time(),
                request_id=request_id,
                status=RequestStatus.ERROR,
                user=str(message.author),
                channel=str(message.channel),
                message_content=message.content,
                error="Forbidden"
            ))
        except discord.HTTPException as e:
            logger.error(f"Discord API error: {e}")
            await self._emit_event(RequestUpdateEvent(
                timestamp=time.time(),
                request_id=request_id,
                status=RequestStatus.ERROR,
                user=str(message.author),
                channel=str(message.channel),
                message_content=message.content,
                error=str(e)
            ))
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            await self._emit_event(RequestUpdateEvent(
                timestamp=time.time(),
                request_id=request_id,
                status=RequestStatus.ERROR,
                user=str(message.author),
                channel=str(message.channel),
                message_content=message.content,
                error=str(e)
            ))
            try:
                await message.reply(f"❌ Error processing message: {str(e)}", mention_author=False)
            except:
                pass
