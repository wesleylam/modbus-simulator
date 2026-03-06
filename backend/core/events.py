import asyncio
import time
from dataclasses import dataclass


@dataclass
class RegisterChangeEvent:
    address: int
    old_value: int | bool
    new_value: int | bool
    source: str           # "modbus" | "api"
    client_ip: str | None
    timestamp: float = 0.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()

    def to_dict(self) -> dict:
        return {
            "type": "update",
            "address": self.address,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "source": self.source,
            "client_ip": self.client_ip,
            "timestamp": self.timestamp,
        }


# Global event bus — producers push, WebSocket broadcaster consumes
event_bus: asyncio.Queue[RegisterChangeEvent] = asyncio.Queue()
