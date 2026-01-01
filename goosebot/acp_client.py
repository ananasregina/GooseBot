"""
ACP (Agent Client Protocol) client for Goose AI
Communicates with goose acp subprocess via stdio (JSON-RPC 2.0)
"""
import asyncio
import json
from typing import Optional, Tuple, List, Callable, Any, Awaitable
import subprocess
import os

try:
    from goosebot.config import Config
    from goosebot.utils.logger import setup_logger
except ImportError:
    from config import Config
    from utils.logger import setup_logger

logger = setup_logger(__name__)


class ACPClient:
    """Client for communicating with goose acp subprocess"""

    def __init__(self, goose_path: Optional[str] = None, env_vars: Optional[dict] = None):
        self.goose_path = goose_path or Config.GOOSE_CLI_PATH
        self.env_vars = env_vars or {}
        self._process: Optional[asyncio.subprocess.Process] = None
        self._request_id = 0
        self._write_lock = asyncio.Lock()
        self._initialized = False
        self._shutdown = False
        self.capabilities: dict = {}

    async def start(self):
        """Start goose acp subprocess"""
        if self._process is not None:
            logger.warning("ACP subprocess already running")
            return

        cmd = [self.goose_path, "acp"]

        logger.info(f"Starting goose acp: {' '.join(cmd)}")

        # Prepare environment
        env = os.environ.copy()
        if self.env_vars:
            env.update(self.env_vars)

        self._process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        if self._process:
            asyncio.create_task(self._monitor_stderr())

        await self.initialize()

    async def _monitor_stderr(self):
        """Monitor stderr from acp subprocess"""
        proc = self._process
        if not proc:
            return

        async for line in proc.stderr:
            line = line.decode().strip()
            if line:
                logger.info(f"Goose stderr: {line}")

    async def _read_line(self) -> Optional[str]:
        """Read a single line from stdout"""
        proc = self._process
        if not proc:
            return None

        if proc.stdout.at_eof():
            return None

        line = await proc.stdout.readline()
        if not line:
            return None
        return line.decode().strip()

    async def send_request(self, method: str, params: Optional[dict] = None, 
                     collect_notifications: bool = False,
                     on_notification: Optional[Callable[[dict], Awaitable[None]]] = None) -> Tuple[Optional[dict], List[dict]]:
        """Send a JSON-RPC 2.0 request and wait for response
        
        Args:
            method: The RPC method name
            params: Optional parameters for the request
            collect_notifications: If True, collect notifications until response arrives
            on_notification: Optional async callback(notification_dict) for real-time processing
            
        Returns:
            Tuple of (response, notifications) if collect_notifications is True,
            otherwise just (response, [])
        """
        proc = self._process
        if not proc:
            logger.error("ACP process not running")
            return None, []

        async with self._write_lock:
            if self._shutdown:
                logger.error("ACP is shut down, cannot send request")
                return None, []

            self._request_id += 1
            request = {
                "jsonrpc": "2.0",
                "method": method,
                "id": self._request_id,
            }
            if params:
                request["params"] = params

            request_str = json.dumps(request)
            logger.debug(f">>> Sending: {request_str}")

            proc.stdin.write(request_str.encode() + b'\n')
            await proc.stdin.drain()

            notifications = []

            while True:
                line = await self._read_line()
                if line is None:
                    if collect_notifications:
                        return None, notifications
                    return None, []

                try:
                    response = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON: {e}")
                    logger.error(f"Line was: {line[:200]}")
                    continue

                # Check if this is a notification (has 'method' but no 'id')
                if 'method' in response and 'id' not in response:
                    # Log less aggressively for chunks
                    is_chunk = response.get('method') == 'session/update' and 'agentMessageChunk' in str(response)
                    if not is_chunk:
                         logger.debug(f"<<< Notification: {response.get('method')}")
                    
                    if on_notification:
                        await on_notification(response)
                        
                    if collect_notifications:
                        notifications.append(response)
                    continue

                if response.get('id') == self._request_id:
                    logger.debug(f"<<< Response: {line}")
                    if collect_notifications:
                        return response, notifications
                    return response, []
                else:
                    # Response for a different request ID, skip
                    logger.debug(f"<<< Ignoring response for ID {response.get('id')}, waiting for {self._request_id}")

    async def initialize(self) -> bool:
        """Initialize ACP connection and verify capabilities"""
        response, _ = await self.send_request("initialize", {
            "protocolVersion": "v1",
            "clientCapabilities": {},
            "clientInfo": {
                "name": "goosebot",
                "version": "1.0.0"
            }
        })

        if response and 'result' in response:
            capabilities = response['result'].get('agentCapabilities', {})
            load_session = capabilities.get('loadSession', False)
            prompt_caps = capabilities.get('promptCapabilities', {})

            logger.info(f"Initialized ACP: loadSession={load_session}, promptCapabilities={prompt_caps}")
            self.capabilities = capabilities
            self._initialized = True
            return True
        else:
            error = response.get('error', {}) if response else {}
            logger.error(f"Failed to initialize ACP: {error}")
            return False

    async def new_session(self, cwd: Optional[str] = None, instructions: Optional[str] = None) -> Optional[str]:
        """Create a new session (session/new)"""
        params = {
            "mcpServers": [],
            "cwd": cwd or os.getcwd()
        }
        if instructions:
            params["instructions"] = instructions
        
        response, _ = await self.send_request("session/new", params)
        
        if response and 'result' in response:
            session_id = response['result'].get('sessionId')
            logger.info(f"Created new session: {session_id}")
            return session_id
        else:
            error = response.get('error', {}) if response else {}
            logger.error(f"Failed to create session: {error}")
            return None

    async def load_session(self, session_id: str, cwd: Optional[str] = None) -> Tuple[bool, List[dict]]:
        """Load an existing session (session/load)
        
        Returns:
            Tuple of (success, notifications) where notifications contain session history
        """
        params = {
            "sessionId": session_id,
            "mcpServers": [],
            "cwd": cwd or os.getcwd()
        }
        
        response, notifications = await self.send_request("session/load", params, collect_notifications=True)
        
        if response and 'result' in response:
            logger.info(f"Loaded session: {session_id} ({len(notifications)} history notifications)")
            return True, notifications
        else:
            error = response.get('error', {}) if response else {}
            logger.error(f"Failed to load session {session_id}: {error}")
            return False, []

    async def prompt(self, session_id: str, text: str, 
                chunk_callback: Optional[Callable] = None) -> Optional[dict]:
        """Send a prompt to a session (session/prompt)
        
        Args:
            session_id: The session ID to send prompt to
            text: The user's message/prompt
            chunk_callback: Optional async callback(text) called for each response chunk
            
        Returns:
            The final response result, or None if error
        """
        async def handle_notification(notification: dict):
            """Handle streaming notifications in real-time"""
            method = notification.get('method')
            
            if method in ["session/notification", "session/update"]:
                params = notification.get('params', {})
                
                # Try to extract the update object
                if 'update' in params:
                    update = params['update']
                elif 'sessionUpdate' in params:
                    # Sometimes params itself might be the update object
                    update = params
                else:
                    update = {}
                
                if not isinstance(update, dict):
                    return
                
                update_type = update.get('sessionUpdate', 'unknown')
                content = update.get('content')
                
                if update_type in ["agentMessageChunk", "agent_message_chunk"]:
                    # Stream text content to callback
                    if isinstance(content, dict):
                        text = content.get('text', '')
                        if text and chunk_callback:
                            await chunk_callback(text)
                
                elif update_type in ["toolCall", "tool_call"]:
                    logger.debug(f"Tool call: {update}")
                elif update_type in ["toolCallUpdate", "tool_call_update"]:
                    logger.debug(f"Tool call update: {update}")
                elif update_type == "error":
                    logger.error(f"Session error: {update}")
                elif update_type == "complete":
                    logger.debug("Prompt complete")
                elif update_type != "unknown":
                    logger.debug(f"Unknown update type: {update_type}")

        # Send request with real-time notification handler
        # We don't need to collect notifications if we have a callback, limiting memory usage
        collect = chunk_callback is None
        
        # Prepare prompt payload
        if isinstance(text, str):
            prompt_payload = [{"type": "text", "text": text}]
        elif isinstance(text, list):
            prompt_payload = text
        else:
            logger.error(f"Invalid prompt type: {type(text)}")
            return None

        response, notifications = await self.send_request("session/prompt", {
            "sessionId": session_id,
            "prompt": prompt_payload
        }, collect_notifications=collect, on_notification=handle_notification)

        if response and 'error' in response:
            logger.error(f"Prompt error: {response['error']}")
        
        return response

    async def cancel(self, session_id: str) -> bool:
        """Cancel in-progress prompt (session/cancel)"""
        response, _ = await self.send_request("session/cancel", {
            "sessionId": session_id
        })
        
        if response and 'result' in response:
            logger.info(f"Cancelled prompt for session: {session_id}")
            return True
        else:
            error = response.get('error', {}) if response else {}
            logger.error(f"Failed to cancel session {session_id}: {error}")
            return False

    async def stop(self):
        """Stop the ACP subprocess"""
        self._shutdown = True
        
        proc = self._process
        if proc:
            try:
                proc.terminate()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.wait()
                logger.info("Goose acp subprocess stopped")
            except Exception as e:
                logger.error(f"Error stopping acp process: {e}")
            finally:
                self._process = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()
