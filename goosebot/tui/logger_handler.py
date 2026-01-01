import logging
import asyncio
import time
from .events import LogEvent

class TUILogHandler(logging.Handler):
    """A logging handler that sends logs to the TUI event queue"""
    
    def __init__(self, event_queue: asyncio.Queue):
        super().__init__()
        self.event_queue = event_queue
        self.loop = asyncio.get_event_loop()

    def emit(self, record):
        try:
            msg = self.format(record)
            event = LogEvent(
                timestamp=time.time(),
                level=record.levelname,
                message=msg,
                logger_name=record.name
            )
            # Use thread-safe queue putting if we're not in the main loop
            # But the bot is usually async.
            try:
                self.event_queue.put_nowait(event)
            except asyncio.QueueFull:
                pass
        except Exception:
            self.handleError(record)
