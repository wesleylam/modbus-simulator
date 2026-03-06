import asyncio
import logging
import threading
from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusServerContext, ModbusSlaveContext

from .datablock import StoreBackedDataBlock

logger = logging.getLogger(__name__)

# Module-level references so the running Modbus server (if any) can be
# notified when the configured unit ID changes from the API.
_context = None
_slave_ctx = None
_context_lock = threading.Lock()
_current_unit_id = None


class DynamicModbusContext(ModbusServerContext):
    """
    A ModbusServerContext that always routes requests to the single slave
    context, but only accepts requests matching store.unit_id.
    Requests with any other unit ID get a 'device not found' response.
    """

    def __init__(self, slave_ctx, store):
        # single=False so pymodbus routes by unit ID
        super().__init__(slaves={store.unit_id: slave_ctx}, single=False)
        self._slave_ctx = slave_ctx
        self._store = store

    def __getitem__(self, unit_id: int):
        """Called by pymodbus for every incoming request."""
        current_uid = self._store.unit_id
        if unit_id == current_uid or unit_id == 0:  # 0 = broadcast
            return self._slave_ctx
        raise KeyError(f"Unit ID {unit_id} not configured (current: {current_uid})")

    def __setitem__(self, unit_id, context):
        pass  # ignore — we manage the slave manually


def start_modbus_server(store, host: str = "0.0.0.0", port: int = 502):
    """
    Start the Modbus TCP slave server (blocking — run in a daemon thread).

    Responds only to requests matching store.unit_id (changeable at runtime).
    Supports FC1–FC6, FC15, FC16.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    coil_block     = StoreBackedDataBlock(store, "coil",     loop)
    discrete_block = StoreBackedDataBlock(store, "discrete", loop)
    holding_block  = StoreBackedDataBlock(store, "holding",  loop)
    input_block    = StoreBackedDataBlock(store, "input",    loop)

    slave_ctx = ModbusSlaveContext(
        di=discrete_block,
        co=coil_block,
        hr=holding_block,
        ir=input_block,
    )

    context = DynamicModbusContext(slave_ctx, store)
    # Save references so other threads (API) can update the active unit ID.
    global _context, _slave_ctx, _current_unit_id
    with _context_lock:
        _context = context
        _slave_ctx = slave_ctx
        _current_unit_id = store.unit_id

    logger.info(f"Modbus TCP server listening on {host}:{port} (unit ID: {store.unit_id})")
    StartTcpServer(context=context, address=(host, port))


def update_unit_id(new_unit_id: int):
    """Update the module-level current unit id and patch the running
    Modbus server context (if present) so it accepts the new unit id.
    This does not restart the TCP listener; only the Modbus context mapping
    is updated so incoming requests for the new unit id are routed.
    """
    global _context, _slave_ctx, _current_unit_id
    with _context_lock:
        _current_unit_id = new_unit_id
        if _context is None:
            return
        # Try to update known internal attributes used by pymodbus. We
        # attempt several likely attribute names to be robust across
        # different pymodbus versions.
        try:
            setattr(_context, "slaves", {new_unit_id: _slave_ctx})
        except Exception:
            pass
        try:
            setattr(_context, "_slaves", {new_unit_id: _slave_ctx})
        except Exception:
            pass


def get_current_unit_id() -> int | None:
    return _current_unit_id
