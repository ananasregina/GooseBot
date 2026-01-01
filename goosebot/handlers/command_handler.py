"""
Slash command handler for Discord bot
"""
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import time
from typing import Optional

try:
    from ..session_manager import SessionManager
    from ..goose_client import GooseClient
    from ..utils.logger import setup_logger
    from ..tui import RequestUpdateEvent, RequestStatus
except ImportError:
    from session_manager import SessionManager
    from goose_client import GooseClient
    from utils.logger import setup_logger
    from tui import RequestUpdateEvent, RequestStatus

logger = setup_logger(__name__)


class CommandHandler(commands.Cog):
    """Handles slash commands for GooseBot"""

    def __init__(self, bot: commands.Bot, session_manager: SessionManager, goose_client: GooseClient, tui_queue: Optional[asyncio.Queue] = None):
        self.bot = bot
        self.session_manager = session_manager
        self.goose_client = goose_client
        self.tui_queue = tui_queue

    async def _emit_event(self, event: RequestUpdateEvent):
        if self.tui_queue:
            await self.tui_queue.put(event)

    @app_commands.command(name="set_name", description="Set the agent name for new sessions in this server")
    async def set_name(self, interaction: discord.Interaction, name: str):
        """Set the agent name for new sessions"""
        request_id = f"cmd_{interaction.id}"
        await self._emit_event(RequestUpdateEvent(
            timestamp=time.time(),
            request_id=request_id,
            status=RequestStatus.PROCESSING,
            user=str(interaction.user),
            channel=str(interaction.channel),
            message_content=f"/set_name {name}",
            progress=0.1
        ))
        
        await interaction.response.defer()

        if not interaction.guild_id:
            await interaction.followup.send("This command can only be used in a server")
            return

        try:
            await self.session_manager.set_agent_name(interaction.guild_id, name)
            await interaction.followup.send(f"✅ Agent name set to: **{name}**")
            logger.info(f"Agent name set to {name} for guild {interaction.guild_id}")
            
            await self._emit_event(RequestUpdateEvent(
                timestamp=time.time(),
                request_id=request_id,
                status=RequestStatus.COMPLETED,
                user=str(interaction.user),
                channel=str(interaction.channel),
                message_content=f"/set_name {name}",
                progress=1.0
            ))
        except Exception as e:
            logger.error(f"Error setting name: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Error: {str(e)}")
            await self._emit_event(RequestUpdateEvent(
                timestamp=time.time(),
                request_id=request_id,
                status=RequestStatus.ERROR,
                user=str(interaction.user),
                channel=str(interaction.channel),
                message_content=f"/set_name {name}",
                error=str(e)
            ))

    @app_commands.command(name="clear_session", description="Clear the current Goose session for this channel")
    async def clear_session(self, interaction: discord.Interaction):
        """Clear the current session"""
        request_id = f"cmd_{interaction.id}"
        await self._emit_event(RequestUpdateEvent(
            timestamp=time.time(),
            request_id=request_id,
            status=RequestStatus.PROCESSING,
            user=str(interaction.user),
            channel=str(interaction.channel),
            message_content="/clear_session",
            progress=0.1
        ))

        await interaction.response.defer()

        if interaction.channel_id is None:
            await interaction.followup.send("⚠️ This command cannot be used in DMs")
            return

        channel_id = interaction.channel_id
        session_info = await self.session_manager.get_session(channel_id)

        if session_info is None:
            await interaction.followup.send("⚠️ No active session in this channel")
            return

        try:
            await self.goose_client.delete_session(session_info.session_name)
            await self.session_manager.clear_session(channel_id)
            await interaction.followup.send("🧹 Session cleared for this channel")
            logger.info(f"Cleared session for channel {channel_id}")
            
            await self._emit_event(RequestUpdateEvent(
                timestamp=time.time(),
                request_id=request_id,
                status=RequestStatus.COMPLETED,
                user=str(interaction.user),
                channel=str(interaction.channel),
                message_content="/clear_session",
                progress=1.0
            ))
        except Exception as e:
            logger.error(f"Error clearing session: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Error: {str(e)}")
            await self._emit_event(RequestUpdateEvent(
                timestamp=time.time(),
                request_id=request_id,
                status=RequestStatus.ERROR,
                user=str(interaction.user),
                channel=str(interaction.channel),
                message_content="/clear_session",
                error=str(e)
            ))

    @app_commands.command(name="restart_session", description="Restart the Goose session (clear and create new)")
    async def restart_session(self, interaction: discord.Interaction):
        """Restart the session"""
        request_id = f"cmd_{interaction.id}"
        await self._emit_event(RequestUpdateEvent(
            timestamp=time.time(),
            request_id=request_id,
            status=RequestStatus.PROCESSING,
            user=str(interaction.user),
            channel=str(interaction.channel),
            message_content="/restart_session",
            progress=0.1
        ))

        await interaction.response.defer()

        if interaction.channel_id is None:
            await interaction.followup.send("⚠️ This command cannot be used in DMs")
            return

        channel_id = interaction.channel_id
        session_info = await self.session_manager.get_session(channel_id)

        if session_info is None:
            await interaction.followup.send("⚠️ No active session in this channel")
            return

        try:
            # Delete and then it will be re-created on next message
            await self.goose_client.delete_session(session_info.session_name)
            await self.session_manager.clear_session(channel_id)
            await interaction.followup.send("🔄 Session restarted! A new session will be created on your next message.")
            logger.info(f"Restarted session for channel {channel_id}")
            
            await self._emit_event(RequestUpdateEvent(
                timestamp=time.time(),
                request_id=request_id,
                status=RequestStatus.COMPLETED,
                user=str(interaction.user),
                channel=str(interaction.channel),
                message_content="/restart_session",
                progress=1.0
            ))
        except Exception as e:
            logger.error(f"Error restarting session: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Error: {str(e)}")
            await self._emit_event(RequestUpdateEvent(
                timestamp=time.time(),
                request_id=request_id,
                status=RequestStatus.ERROR,
                user=str(interaction.user),
                channel=str(interaction.channel),
                message_content="/restart_session",
                error=str(e)
            ))

    @app_commands.command(name="compact", description="Manually trigger session compaction to save context tokens")
    async def compact(self, interaction: discord.Interaction):
        """Compact the session"""
        request_id = f"cmd_{interaction.id}"
        await self._emit_event(RequestUpdateEvent(
            timestamp=time.time(),
            request_id=request_id,
            status=RequestStatus.PROCESSING,
            user=str(interaction.user),
            channel=str(interaction.channel),
            message_content="/compact",
            progress=0.1
        ))

        await interaction.response.defer()

        if interaction.channel_id is None:
            await interaction.followup.send("⚠️ This command cannot be used in DMs")
            return

        channel_id = interaction.channel_id
        session_info = await self.session_manager.get_session(channel_id)

        if session_info is None:
            await interaction.followup.send("⚠️ No active session in this channel")
            return

        try:
            await self.goose_client.compact_session(session_info.session_name)
            await interaction.followup.send("📦 Session context compacted!")
            logger.info(f"Compacted session {session_info.session_name}")
            
            await self._emit_event(RequestUpdateEvent(
                timestamp=time.time(),
                request_id=request_id,
                status=RequestStatus.COMPLETED,
                user=str(interaction.user),
                channel=str(interaction.channel),
                message_content="/compact",
                progress=1.0
            ))
        except Exception as e:
            logger.error(f"Error compacting session: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Error: {str(e)}")
            await self._emit_event(RequestUpdateEvent(
                timestamp=time.time(),
                request_id=request_id,
                status=RequestStatus.ERROR,
                user=str(interaction.user),
                channel=str(interaction.channel),
                message_content="/compact",
                error=str(e)
            ))

    @app_commands.command(name="capy", description="Get fresh, delicious Capybara facts and news!")
    async def capy(self, interaction: discord.Interaction):
        """Get Capybara news and facts with streaming"""
        request_id = f"cmd_{interaction.id}"
        await self._emit_event(RequestUpdateEvent(
            timestamp=time.time(),
            request_id=request_id,
            status=RequestStatus.PROCESSING,
            user=str(interaction.user),
            channel=str(interaction.channel),
            message_content="/capy",
            progress=0.1
        ))
        
        await interaction.response.defer()

        full_response_text = ""
        last_update_time = 0.0

        async def chunk_callback(chunk_text: str):
            """Callback for streaming response chunks to Discord"""
            nonlocal full_response_text, last_update_time
            
            full_response_text += chunk_text
            current_time = time.time()
            
            # Throttle updates to avoid rate limits (approx 1 per second)
            if current_time - last_update_time >= 1.0:
                try:
                    await interaction.edit_original_response(content=full_response_text)
                    last_update_time = current_time
                    
                    # Update TUI status to RESPONDING
                    await self._emit_event(RequestUpdateEvent(
                        timestamp=current_time,
                        request_id=request_id,
                        status=RequestStatus.RESPONDING,
                        user=str(interaction.user),
                        channel=str(interaction.channel),
                        message_content="/capy",
                        progress=min(0.9, 0.1 + (len(full_response_text) / 2000))
                    ))
                except discord.HTTPException as e:
                    logger.warning(f"Failed to update chunk: {e}")

        try:
            async with interaction.channel.typing():
                # We use a temporary session name for this request
                temp_session = f"capy-news-{interaction.user.id}-{int(time.time())}"
                prompt = (
                    "Please perform a web search to find 3 interesting, up-to-date facts about capybaras "
                    "and 1 recent news item involving capybaras. Present the information in a fun, "
                    "charming, and 'delicious' way. Be brief but informative!"
                )
                
                # Emit status update: SEARCHING/PROCESSING
                await self._emit_event(RequestUpdateEvent(
                    timestamp=time.time(),
                    request_id=request_id,
                    status=RequestStatus.PROCESSING,
                    user=str(interaction.user),
                    channel=str(interaction.channel),
                    message_content="/capy",
                    progress=0.3
                ))

                response = await self.goose_client.send_message(
                    session_name=temp_session,
                    message=prompt,
                    resume=False,  # Start a fresh session for news
                    chunk_callback=chunk_callback
                )
            
            # Ensure final response is sent if not already fully Sent via chunks
            if full_response_text:
                await interaction.edit_original_response(content=full_response_text)
            elif response:
                await interaction.edit_original_response(content=response)
            
            logger.info(f"Delivered capy facts to {interaction.user}")
            
            await self._emit_event(RequestUpdateEvent(
                timestamp=time.time(),
                request_id=request_id,
                status=RequestStatus.COMPLETED,
                user=str(interaction.user),
                channel=str(interaction.channel),
                message_content="/capy",
                progress=1.0
            ))
            
        except Exception as e:
            logger.error(f"Error in capy command: {e}", exc_info=True)
            try:
                await interaction.followup.send(f"❌ Error: {str(e)}")
            except:
                pass
            await self._emit_event(RequestUpdateEvent(
                timestamp=time.time(),
                request_id=request_id,
                status=RequestStatus.ERROR,
                user=str(interaction.user),
                channel=str(interaction.channel),
                message_content="/capy",
                error=str(e)
            ))

    @app_commands.command(name="noticias", description="Get the latest news about a specific topic")
    async def noticias(self, interaction: discord.Interaction, tema: str):
        """Get news about a specific topic with analysis"""
        request_id = f"cmd_{interaction.id}"
        await self._emit_event(RequestUpdateEvent(
            timestamp=time.time(),
            request_id=request_id,
            status=RequestStatus.PROCESSING,
            user=str(interaction.user),
            channel=str(interaction.channel),
            message_content=f"/noticias {tema}",
            progress=0.1
        ))
        
        await interaction.response.defer()

        full_response_text = ""
        last_update_time = 0.0

        async def chunk_callback(chunk_text: str):
            """Callback for streaming response chunks to Discord"""
            nonlocal full_response_text, last_update_time
            
            full_response_text += chunk_text
            current_time = time.time()
            
            # Throttle updates to avoid rate limits (approx 1 per second)
            if current_time - last_update_time >= 1.0:
                try:
                    await interaction.edit_original_response(content=full_response_text)
                    last_update_time = current_time
                    
                    # Update TUI status to RESPONDING
                    await self._emit_event(RequestUpdateEvent(
                        timestamp=current_time,
                        request_id=request_id,
                        status=RequestStatus.RESPONDING,
                        user=str(interaction.user),
                        channel=str(interaction.channel),
                        message_content=f"/noticias {tema}",
                        progress=min(0.9, 0.1 + (len(full_response_text) / 2000))
                    ))
                except discord.HTTPException as e:
                    logger.warning(f"Failed to update chunk: {e}")

        try:
            async with interaction.channel.typing():
                # We use a temporary session name for this request
                temp_session = f"news-{interaction.user.id}-{int(time.time())}"
                prompt = (
                    f"Hola amiga, por favor haz una búsqueda de las noticias de actualidad más recientes y relevantes sobre el tema de {tema}. "
                    "Haz un análisis y dime lo que crees que me parecería más importante o digno de conversar, de acuerdo a nuestras memorias existentes."
                )
                
                # Emit status update: SEARCHING/PROCESSING
                await self._emit_event(RequestUpdateEvent(
                    timestamp=time.time(),
                    request_id=request_id,
                    status=RequestStatus.PROCESSING,
                    user=str(interaction.user),
                    channel=str(interaction.channel),
                    message_content=f"/noticias {tema}",
                    progress=0.3
                ))

                response = await self.goose_client.send_message(
                    session_name=temp_session,
                    message=prompt,
                    resume=False,  # Start a fresh session for news
                    chunk_callback=chunk_callback
                )
            
            # Ensure final response is sent if not already fully sent via chunks
            if full_response_text:
                await interaction.edit_original_response(content=full_response_text)
            elif response:
                await interaction.edit_original_response(content=response)
            
            logger.info(f"Delivered news about {tema} to {interaction.user}")
            
            await self._emit_event(RequestUpdateEvent(
                timestamp=time.time(),
                request_id=request_id,
                status=RequestStatus.COMPLETED,
                user=str(interaction.user),
                channel=str(interaction.channel),
                message_content=f"/noticias {tema}",
                progress=1.0
            ))
            
        except Exception as e:
            logger.error(f"Error in noticias command: {e}", exc_info=True)
            try:
                await interaction.followup.send(f"❌ Error: {str(e)}")
            except:
                pass
            await self._emit_event(RequestUpdateEvent(
                timestamp=time.time(),
                request_id=request_id,
                status=RequestStatus.ERROR,
                user=str(interaction.user),
                channel=str(interaction.channel),
                message_content=f"/noticias {tema}",
                error=str(e)
            ))


    @app_commands.command(name="status", description="Show the current session status")
    async def status(self, interaction: discord.Interaction):
        """Show session status"""
        request_id = f"cmd_{interaction.id}"
        await self._emit_event(RequestUpdateEvent(
            timestamp=time.time(),
            request_id=request_id,
            status=RequestStatus.PROCESSING,
            user=str(interaction.user),
            channel=str(interaction.channel),
            message_content="/status",
            progress=0.1
        ))

        await interaction.response.defer()

        if interaction.channel_id is None:
            await interaction.followup.send("⚠️ This command cannot be used in DMs")
            return

        channel_id = interaction.channel_id
        session_info = await self.session_manager.get_session(channel_id)

        if session_info is None:
            await interaction.followup.send("⚠️ No active session in this channel")
            return

        agent_name = await self.session_manager.get_agent_name(
            session_info.guild_id
        )

        embed = discord.Embed(
            title="🪿 Goose Session Status",
            color=discord.Color.blue(),
        )
        embed.add_field(name="Session Name", value=f"`{session_info.session_name}`", inline=False)
        embed.add_field(name="Agent Name", value=agent_name, inline=True)
        embed.add_field(name="Messages", value=str(session_info.message_count), inline=True)
        embed.add_field(name="Channel ID", value=str(channel_id), inline=True)

        await interaction.followup.send(embed=embed)
        
        await self._emit_event(RequestUpdateEvent(
            timestamp=time.time(),
            request_id=request_id,
            status=RequestStatus.COMPLETED,
            user=str(interaction.user),
            channel=str(interaction.channel),
            message_content="/status",
            progress=1.0
        ))

    @app_commands.command(name="help", description="Show available commands")
    async def help_command(self, interaction: discord.Interaction):
        """Show help information"""
        request_id = f"cmd_{interaction.id}"
        await self._emit_event(RequestUpdateEvent(
            timestamp=time.time(),
            request_id=request_id,
            status=RequestStatus.PROCESSING,
            user=str(interaction.user),
            channel=str(interaction.channel),
            message_content="/help",
            progress=0.1
        ))

        await interaction.response.defer()

        embed = discord.Embed(
            title="🪿 GooseBot Help",
            description="I'm your AI assistant powered by Goose.ai! Mention me with `@GooseBot` to chat.",
            color=discord.Color.green(),
        )
        embed.add_field(name="How to use", value="Just mention me in any message!\nExample: `@GooseBot help me write a Python function`", inline=False)
        embed.add_field(name="Slash Commands", value="`/set_name <name>` - Set agent name\n`/clear_session` - Clear current session\n`/restart_session` - Restart session\n`/compact` - Compact session context\n`/capy` - Get capybara facts & news\n`/noticias <tema>` - Get news about a topic\n`/status` - Show session info\n`/help` - Show this help", inline=False)

        await interaction.followup.send(embed=embed)
        
        await self._emit_event(RequestUpdateEvent(
            timestamp=time.time(),
            request_id=request_id,
            status=RequestStatus.COMPLETED,
            user=str(interaction.user),
            channel=str(interaction.channel),
            message_content="/help",
            progress=1.0
        ))
