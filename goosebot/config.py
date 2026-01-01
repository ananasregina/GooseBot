"""
Configuration management for GooseBot
"""
import os
from pathlib import Path
from typing import Optional, Tuple

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = lambda: None

load_dotenv()


class Config:
    """Configuration class for GooseBot"""

    DISCORD_BOT_TOKEN: str = os.getenv("DISCORD_BOT_TOKEN", "")
    GOOSE_CLI_PATH: str = os.getenv("GOOSE_CLI_PATH", "goose")
    DEFAULT_AGENT_NAME: str = os.getenv("DEFAULT_AGENT_NAME", "Goose")

    # Goose CLI settings
    MAX_TURNS: int = int(os.getenv("GOOSE_MAX_TURNS", "1000"))
    GOOSE_MODE: str = os.getenv("GOOSE_MODE", "auto")

    # Bot settings
    BOT_PREFIX: str = os.getenv("BOT_PREFIX", "/")
    LISTEN_WINDOW_SECONDS: int = int(os.getenv("LISTEN_WINDOW_SECONDS", "300"))

    # Data directory
    DATA_DIR: Path = Path(os.getenv("GOOSE_DATA_DIR", str(Path.home() / ".config" / "goosebot")))

    @classmethod
    def ensure_data_dir(cls):
        """Ensure data directory exists"""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate(cls) -> Tuple[bool, str]:
        """Validate configuration"""
        if not cls.DISCORD_BOT_TOKEN:
            return False, "DISCORD_BOT_TOKEN not set in environment"

        return True, "Configuration valid"

    @classmethod
    def get_session_name(cls, guild_id: int, channel_id: int) -> str:
        """Generate session name for Discord channel"""
        return f"discord-{guild_id}-{channel_id}"
