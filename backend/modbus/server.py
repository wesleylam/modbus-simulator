import asyncio
import logging
from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusServerContext, ModbusSlaveContext

from .datablock import StoreBackedDataBlock

logger = logging.getLogger(__name__)


def start_modbus_server(store, host: str = "0.0.0.0", port: int = 502):
    """
    Start the Modbus TCP slave server (blocking — run in a daemon thread).

    Wires four StoreBackedDataBlocks (one per register type) into a single
    ModbusSlaveContext so all function codes are supported:
        FC1  - Read Coils
        FC2  - Read Discrete Inputs
        FC3  - Read Holding Registers
        FC4  - Read Input Registers
        FC5  - Write Single Coil
        FC6  - Write Single Holding Register
        FC15 - Write Multiple Coils
        FC16 - Write Multiple Holding Registers
    """
    loop = asyncio.get_event_loop()

    coil_block     = StoreBackedDataBlock(store, "coil",     loop)
    discrete_block = StoreBackedDataBlock(store, "discrete", loop)
    holding_block  = StoreBackedDataBlock(store, "holding",  loop)
    input_block    = StoreBackedDataBlock(store, "input",    loop)

    slave_ctx = ModbusSlaveContext(
        di=discrete_block,   # Discrete Inputs  (FC2)
        co=coil_block,       # Coils             (FC1, FC5, FC15)
        hr=holding_block,    # Holding Registers (FC3, FC6, FC16)
        ir=input_block,      # Input Registers   (FC4)
    )

    context = ModbusServerContext(slaves=slave_ctx, single=True)

    logger.info(f"Modbus TCP server listening on {host}:{port}")
    StartTcpServer(context=context, address=(host, port))
