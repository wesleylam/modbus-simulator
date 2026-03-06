import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List, Callable, Optional


@dataclass
class Register:
    address: int
    reg_type: str  # coil | discrete | holding | input
    name: str
    value: int | bool
    writable: bool
    last_changed: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "address": self.address,
            "type": self.reg_type,
            "name": self.name,
            "value": self.value,
            "writable": self.writable,
            "last_changed": self.last_changed,
        }


class RegisterStore:
    def __init__(self):
        self._data: Dict[int, Register] = {}
        self._lock = asyncio.Lock()
        self._change_callbacks: List[Callable] = []

    def load(self, registers: List[Register]):
        """Replace the entire register map (called on startup or reload)."""
        self._data = {r.address: r for r in registers}

    def all(self) -> List[Register]:
        return list(self._data.values())

    def get(self, address: int) -> Optional[Register]:
        return self._data.get(address)

    def is_writable(self, address: int) -> bool:
        reg = self._data.get(address)
        return reg is not None and reg.writable

    async def set(self, address: int, value: int | bool, source: str = "api", client_ip: str | None = None) -> tuple:
        """Update a register value and return (old_value, new_value)."""
        async with self._lock:
            reg = self._data.get(address)
            if reg is None:
                raise KeyError(f"Register {address} not found")
            old_value = reg.value
            reg.value = value
            reg.last_changed = time.time()
        # Fire callbacks outside lock
        for cb in self._change_callbacks:
            await cb(address, old_value, value, source, client_ip)
        return old_value, value

    def set_sync(self, address: int, value: int | bool, source: str = "modbus", client_ip: str | None = None):
        """Thread-safe synchronous set — used by the Modbus server thread."""
        reg = self._data.get(address)
        if reg is None:
            return None, None
        old_value = reg.value
        reg.value = value
        reg.last_changed = time.time()
        return old_value, value

    def register_change_callback(self, cb: Callable):
        self._change_callbacks.append(cb)

    def get_values_by_type(self, reg_type: str) -> Dict[int, int | bool]:
        return {
            r.address: r.value
            for r in self._data.values()
            if r.reg_type == reg_type
        }
