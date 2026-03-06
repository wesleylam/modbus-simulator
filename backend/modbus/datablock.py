import asyncio
import time
import logging
from pymodbus.datastore import ModbusSparseDataBlock

from core.events import event_bus, RegisterChangeEvent

logger = logging.getLogger(__name__)


class StoreBackedDataBlock(ModbusSparseDataBlock):
    """
    A pymodbus datablock that reads from and writes to the RegisterStore.
    On any write, it emits a RegisterChangeEvent onto the async event bus
    so the dashboard WebSocket gets notified in real-time.
    """

    def __init__(self, store, reg_type: str, loop: asyncio.AbstractEventLoop):
        self._store = store
        self._reg_type = reg_type
        self._loop = loop

        # Seed the datablock with current values from the store
        initial = store.get_values_by_type(reg_type)
        values = initial if initial else {0: 0}
        super().__init__(values)

    def setValues(self, address: int, values: list, context=None):
        old_values = self.getValues(address, len(values))
        super().setValues(address, values)

        for i, (old_val, new_val) in enumerate(zip(old_values, values)):
            addr = address + i
            if old_val == new_val:
                continue

            # Update the RegisterStore synchronously (we're in a thread)
            self._store.set_sync(addr, new_val, source="modbus")

            # Emit change event to the async event bus from this thread
            evt = RegisterChangeEvent(
                address=addr,
                old_value=old_val,
                new_value=new_val,
                source="modbus",
                client_ip=None,
                timestamp=time.time(),
            )
            try:
                asyncio.run_coroutine_threadsafe(event_bus.put(evt), self._loop)
            except Exception as e:
                logger.warning(f"Failed to emit change event: {e}")
