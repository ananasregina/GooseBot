import dataclasses
from enum import Enum
from typing import Optional

class RequestStatus(Enum):
    RECEIVED = "received"
    QUEUING = "queuing"
    PROCESSING = "processing"
    RESPONDING = "responding"
    COMPLETED = "completed"
    ERROR = "error"

@dataclasses.dataclass
class BotEvent:
    """Base class for bot events"""
    timestamp: float

@dataclasses.dataclass
class RequestUpdateEvent(BotEvent):
    """Event for request status updates"""
    request_id: str
    status: RequestStatus
    user: str
    channel: str
    message_content: str
    progress: float = 0.0 # 0.0 to 1.0
    error: Optional[str] = None

@dataclasses.dataclass
class LogEvent(BotEvent):
    """Event for log messages"""
    level: str
    message: str
    logger_name: str

@dataclasses.dataclass
class BotStatusEvent(BotEvent):
    """Event for overall bot status"""
    is_connected: bool
    guild_count: int
    user_name: str
