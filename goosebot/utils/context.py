"""
Utility for generating context-aware instructions for Goose sessions
"""
import discord
from typing import Optional

def get_context_instructions(
    member: discord.Member, 
    channel: discord.abc.Messageable, 
    guild: Optional[discord.Guild] = None,
    bot_user: Optional[discord.ClientUser] = None
) -> str:
    """Generate context instructions for the agent"""
    # 1. Get Human-readable names
    guild_name = guild.name if guild else "Direct Message"
    
    # 2. Handle different channel types
    if isinstance(channel, discord.DMChannel):
        channel_name = f"Direct Message with {channel.recipient}"
    elif hasattr(channel, "name"):
        channel_name = channel.name
    else:
        # Fallback to string representation which usually contains the name for most types
        channel_name = str(channel)

    # 3. Get human-readable user names
    # Priority: display_name (nickname) > global_name > name (username) > str fallback
    user_name = (
        getattr(member, "display_name", None) or 
        getattr(member, "global_name", None) or 
        getattr(member, "name", None) or 
        str(member)
    )
    
    bot_name = (
        getattr(bot_user, "display_name", None) or 
        getattr(bot_user, "name", None) or 
        "GooseBot"
    )

    return (
        f"You are interacting as a Discord bot named '{bot_name}'. "
        f"Current Server: '{guild_name}' (ID: {guild.id if guild else 'N/A'}). "
        f"Current Channel: '{channel_name}' (ID: {getattr(channel, 'id', 'N/A')}). "
        f"User talking to you: '{user_name}' (ID: {member.id}). "
        "IMPORTANT: When referring to yourself, use your name. When referring to the user, use their name. "
        "Avoid using raw IDs like <@ID> unless explicitly asked to generate a mention."
    )
