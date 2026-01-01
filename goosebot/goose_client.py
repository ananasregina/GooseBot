"""
Goose CLI client wrapper using ACP (Agent Client Protocol) mode
"""
import asyncio
import json
from typing import Optional
import os

try:
    from goosebot.acp_client import ACPClient
    from goosebot.config import Config
    from goosebot.utils.logger import setup_logger
except ImportError:
    from acp_client import ACPClient
    from config import Config
    from utils.logger import setup_logger

logger = setup_logger(__name__)


class GooseClient:
    """Wrapper for interacting with Goose CLI via ACP protocol"""

    def __init__(self, goose_path: Optional[str] = None):
        self.goose_path = goose_path or Config.GOOSE_CLI_PATH
        self._lock = asyncio.Lock()
        self._acp_client = ACPClient(goose_path=self.goose_path)
        self._started = False
        self._session_mapping = {}
        self._loaded_sessions = set()  # Track sessions loaded in current process

        Config.ensure_data_dir()
        self._load_sessions()

    async def start(self):
        """Start of goose acp subprocess"""
        if self._started:
            logger.warning("Goose ACP already started")
            return

        await self._acp_client.start()
        self._started = True

    async def stop(self):
        """Stop of goose acp subprocess"""
        if self._started:
            await self._acp_client.stop()
            self._started = False

    async def _ensure_started(self):
        """Ensure that ACP client is started"""
        if not self._started:
            await self.start()

    async def _new_session_and_map(self, session_name: str) -> Optional[str]:
        """Create a new session and map Discord channel name to goose session ID"""
        params = {
            "mcpServers": [],
            "cwd": os.getcwd()
        }
        
        response, _ = await self._acp_client.send_request("session/new", params)
        
        if response and 'result' in response:
            session_id = response['result'].get('sessionId')
            logger.info(f"Created new session: {session_id}")
            self._session_mapping[session_name] = session_id
            self._loaded_sessions.add(session_id)
            self._save_sessions()
            return session_id
        else:
            error = response.get('error', {}) if response else {}
            logger.error(f"Failed to create session: {error}")
            return None

    def _get_session_file(self):
        return Config.DATA_DIR / "client_sessions.json"

    def _load_sessions(self):
        """Load session mappings from disk"""
        try:
            session_file = self._get_session_file()
            if not session_file.exists():
                return

            import json
            with open(session_file, 'r') as f:
                self._session_mapping = json.load(f)
            logger.info(f"Loaded {len(self._session_mapping)} session mappings from disk")
        except Exception as e:
            logger.error(f"Failed to load session mappings: {e}")

    def _save_sessions(self):
        """Save session mappings to disk"""
        try:
            import json
            session_file = self._get_session_file()
            with open(session_file, 'w') as f:
                json.dump(self._session_mapping, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save session mappings: {e}")

    async def send_message(
        self,
        session_name: str,
        message: str,
        resume: bool = True,
        chunk_callback=None,
    ) -> str:
        """Send a message to Goose and get response via ACP protocol
        
        Args:
            session_name: The Discord session name
            message: The user message to send
            resume: Whether to resume existing session
            chunk_callback: Optional async callback(text) called for each response chunk
            
        Returns:
            The final response text, or error message
        """
        async with self._lock:
            await self._ensure_started()

            actual_session_id = self._session_mapping.get(session_name)
            
            if not actual_session_id:
                # Create new session and map it
                session_id = await self._new_session_and_map(session_name)
                if not session_id:
                    return "❌ Failed to create session"
            else:
                session_id = actual_session_id
                
                # Check if we need to load this session into active memory
                if session_id not in self._loaded_sessions:
                    success, _ = await self._acp_client.load_session(session_id)
                    if success:
                        self._loaded_sessions.add(session_id)
                    else:
                        logger.warning(f"Failed to load session {session_id}, creating new one")
                        # Session likely deleted or invalid, create new one
                        session_id = await self._new_session_and_map(session_name)
                        if not session_id:
                            return "❌ Failed to create replacement session"
            
            # Send prompt with streaming using the goose-generated session ID
            response = await self._acp_client.prompt(session_id, message, chunk_callback)
            
            if response and 'result' in response:
                result = response['result']
                
                # Result can be either a string (success) or an object with details
                if isinstance(result, str):
                    return result
                elif isinstance(result, dict):
                    # Check for error message
                    if 'error' in result:
                        error_msg = result['error']
                        logger.error(f"Goose ACP error: {error_msg}")
                        return f"❌ Goose error: {error_msg}"
                    
                    # For non-error dicts (like tool calls or empty stops), return empty string
                    # The content should have been streamed via chunks
                    logger.debug(f"Goose response (dict): {result}")
                    return ""
                else:
                    logger.debug(f"Goose response type: {type(result)}")
                    return ""
            elif response and 'error' in response:
                error = response['error']
                logger.error(f"Goose ACP error: {error}")
                return f"❌ Goose error: {error}"
            else:
                logger.error(f"Unexpected ACP response: {response}")
                return "❌ Unexpected response from Goose"

    async def delete_session(self, session_name: str) -> bool:
        """Delete a Goose session - NOT SUPPORTED IN ACP MODE
        
        ACP doesn't provide session deletion - sessions persist until user
        manually cleans them up via 'goose session remove'
        """
        logger.warning(f"Session deletion not supported in ACP mode. Session '{session_name}' will persist.")
        logger.info("Use 'goose session list' and 'goose session remove' to manage sessions manually.")
        return False

    async def create_session(self, session_name: str, agent_name: Optional[str] = None) -> bool:
        """Create a new Goose session"""
        async with self._lock:
            await self._ensure_started()

            # ACP creates session when we first send a prompt
            # Just verify we can connect and have the session ready
            if not self._acp_client._initialized:
                initialized = await self._acp_client.initialize()
                if not initialized:
                    logger.error("Failed to initialize ACP connection")
                    return False
            
            logger.info(f"Session '{session_name}' will be created on first prompt")
            return True

    async def list_sessions(self) -> list[str]:
        """List all Goose sessions - NOT SUPPORTED IN ACP MODE
        
        ACP doesn't provide session listing - we manage sessions ourselves
        """
        logger.debug("Session listing not available in ACP mode")
        return []

    async def session_exists(self, session_name: str) -> bool:
        """Check if a Goose session exists"""
        async with self._lock:
            await self._ensure_started()

            # Session exists if we have it mapped
            return session_name in self._session_mapping

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()
