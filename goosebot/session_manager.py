"""
Session manager for tracking Discord channel → Goose session mappings
"""
import asyncio
import time
from typing import Dict, Optional
from dataclasses import dataclass, field

try:
    from goosebot.config import Config
    from goosebot.utils.logger import setup_logger
except ImportError:
    from config import Config
    from utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class SessionInfo:
    """Information about a Discord-Goose session"""

    session_name: str
    guild_id: int
    channel_id: int
    agent_name: str = ""
    created_at: float = 0.0
    message_count: int = 0
    last_bot_activity: float = 0.0

    def __post_init__(self):
        if not self.agent_name:
            self.agent_name = Config.DEFAULT_AGENT_NAME
        if self.created_at == 0.0:
            self.created_at = time.time()




class SessionManager:
    """Manages Discord channel to Goose session mappings"""

    def __init__(self):
        self._sessions: Dict[int, SessionInfo] = {}
        self._lock = asyncio.Lock()
        self._agent_names: Dict[int, str] = {}
        
        Config.ensure_data_dir()
        self._load_state()

    def _get_state_file(self):
        return Config.DATA_DIR / "sessions.json"

    def _load_state(self):
        """Load state from JSON file"""
        try:
            state_file = self._get_state_file()
            if not state_file.exists():
                return

            import json
            with open(state_file, 'r') as f:
                data = json.load(f)
                
            # Load agent names
            self._agent_names = {int(k): v for k, v in data.get('agent_names', {}).items()}
            
            # Load sessions
            from dataclasses import asdict
            for channel_id, session_data in data.get('sessions', {}).items():
                self._sessions[int(channel_id)] = SessionInfo(**session_data)
                
            logger.info(f"Loaded {len(self._sessions)} sessions from state file")
        except Exception as e:
            logger.error(f"Failed to load state: {e}")

    def _save_state(self):
        """Save state to JSON file"""
        try:
            import json
            from dataclasses import asdict
            
            state_file = self._get_state_file()
            
            data = {
                'agent_names': self._agent_names,
                'sessions': {str(k): asdict(v) for k, v in self._sessions.items()}
            }
            
            with open(state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    async def get_session(self, channel_id: int) -> Optional[SessionInfo]:
        """Get session info for a channel"""
        async with self._lock:
            return self._sessions.get(channel_id)

    async def create_session(
        self,
        guild_id: int,
        channel_id: int,
        agent_name: Optional[str] = None,
    ) -> SessionInfo:
        """Create a new session for a channel"""
        async with self._lock:
            session_name = Config.get_session_name(guild_id, channel_id)
            name = agent_name or self._agent_names.get(
                guild_id, Config.DEFAULT_AGENT_NAME
            )
            if not name:
                name = Config.DEFAULT_AGENT_NAME

            session_info = SessionInfo(
                session_name=session_name,
                guild_id=guild_id,
                channel_id=channel_id,
                agent_name=name,
            )

            self._sessions[channel_id] = session_info
            self._save_state()
            logger.info(f"Created session {session_name} for channel {channel_id}")
            return session_info

    async def clear_session(self, channel_id: int) -> bool:
        """Clear session for a channel"""
        async with self._lock:
            if channel_id in self._sessions:
                session_info = self._sessions.pop(channel_id)
                self._save_state()
                logger.info(f"Cleared session {session_info.session_name}")
                return True
            return False

    async def set_agent_name(self, guild_id: int, agent_name: str):
        """Set the agent name for a guild"""
        async with self._lock:
            self._agent_names[guild_id] = agent_name
            self._save_state()
            logger.info(f"Set agent name for guild {guild_id} to {agent_name}")

    async def get_agent_name(self, guild_id: int) -> str:
        """Get the agent name for a guild"""
        async with self._lock:
            return self._agent_names.get(guild_id, Config.DEFAULT_AGENT_NAME) or Config.DEFAULT_AGENT_NAME

    async def increment_message_count(self, channel_id: int):
        """Increment message count for a session"""
        async with self._lock:
            if channel_id in self._sessions:
                self._sessions[channel_id].message_count += 1
                self._save_state()

    async def update_activity(self, channel_id: int):
        """Update the last bot activity timestamp for a session"""
        async with self._lock:
            if channel_id in self._sessions:
                self._sessions[channel_id].last_bot_activity = time.time()
                self._save_state()
