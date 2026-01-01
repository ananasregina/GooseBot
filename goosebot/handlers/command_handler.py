"""
Slash command handler for Discord bot
"""
import discord
from discord import app_commands
from discord.ext import commands

try:
    from ..session_manager import SessionManager
    from ..goose_client import GooseClient
    from ..utils.logger import setup_logger
except ImportError:
    from session_manager import SessionManager
    from goose_client import GooseClient
    from utils.logger import setup_logger

logger = setup_logger(__name__)


class CommandHandler(commands.Cog):
    """Handles slash commands for GooseBot"""

    def __init__(self, bot: commands.Bot, session_manager: SessionManager, goose_client: GooseClient):
        self.bot = bot
        self.session_manager = session_manager
        self.goose_client = goose_client

    @app_commands.command(name="set_name", description="Set the agent name for new sessions in this server")
    async def set_name(self, interaction: discord.Interaction, name: str):
        """Set the agent name for new sessions"""
        await interaction.response.defer()

        if not interaction.guild_id:
            await interaction.followup.send("This command can only be used in a server")
            return

        try:
            await self.session_manager.set_agent_name(interaction.guild_id, name)
            await interaction.followup.send(f"✅ Agent name set to: **{name}**")
            logger.info(f"Agent name set to {name} for guild {interaction.guild_id}")
        except Exception as e:
            logger.error(f"Error setting name: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Error: {str(e)}")

    @app_commands.command(name="clear_session", description="Clear the current Goose session for this channel")
    async def clear_session(self, interaction: discord.Interaction):
        """Clear the current session"""
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
            await self.session_manager.delete_session(channel_id)
            await interaction.followup.send("✅ Session cleared successfully")
            logger.info(f"Cleared session {session_info.session_name}")
        except Exception as e:
            logger.error(f"Error clearing session: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Error: {str(e)}")

    @app_commands.command(name="restart_session", description="Restart the Goose session (clear and create new)")
    async def restart_session(self, interaction: discord.Interaction):
        """Restart the session"""
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
            await self.session_manager.delete_session(channel_id)

            guild_id = interaction.guild_id if interaction.guild_id else 0
            new_session = await self.session_manager.create_session(guild_id, channel_id)

            await interaction.followup.send("✅ Session restarted successfully")
            logger.info(f"Restarted session, new session: {new_session.session_name} (will be created on next message)")
        except Exception as e:
            logger.error(f"Error restarting session: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Error: {str(e)}")

    @app_commands.command(name="compact", description="Manually trigger session compaction to save context tokens")
    async def compact(self, interaction: discord.Interaction):
        """Compact the session"""
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
            result = await self.goose_client.compact_session(session_info.session_name)
            await interaction.followup.send(result)
            logger.info(f"Compact session result for {session_info.session_name}: {result}")
        except Exception as e:
            logger.error(f"Error compacting session: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Error: {str(e)}")

    @app_commands.command(name="status", description="Show the current session status")
    async def status(self, interaction: discord.Interaction):
        """Show session status"""
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

    @app_commands.command(name="help", description="Show available commands")
    async def help_command(self, interaction: discord.Interaction):
        """Show help information"""
        await interaction.response.defer()

        embed = discord.Embed(
            title="🪿 GooseBot Help",
            description="I'm your AI assistant powered by Goose.ai! Mention me with `@GooseBot` to chat.",
            color=discord.Color.green(),
        )
        embed.add_field(name="How to use", value="Just mention me in any message!\nExample: `@GooseBot help me write a Python function`", inline=False)
        embed.add_field(name="Slash Commands", value="`/set_name <name>` - Set agent name\n`/clear_session` - Clear current session\n`/restart_session` - Restart session\n`/compact` - Compact session context\n`/status` - Show session info\n`/help` - Show this help", inline=False)

        await interaction.followup.send(embed=embed)
