import asyncio
import pytest
from core.store import RegisterStore, Register
from modbus.datablock import StoreBackedDataBlock


@pytest.mark.asyncio
async def test_datablock_getvalues_reads_live_store_values():
    """
    Tests that StoreBackedDataBlock.getValues() always reads the current, live
    value from the store, reflecting changes made by other parts of the app
    (like the API) after the datablock was initialized.
    """
    # 1. Arrange: Create a store and a datablock
    loop = asyncio.get_running_loop()
    store = RegisterStore()
    store.load([Register(address=10, reg_type="holding", name="live_val", value=123, writable=True)])
    datablock = StoreBackedDataBlock(store, "holding", loop)

    # Verify initial state
    assert datablock.getValues(10, 1) == [123]

    # 2. Act: Directly update the store, simulating an API call
    await store.set(10, 999, source="api")

    # 3. Assert: The datablock should return the new value, not the initial one.
    live_value = datablock.getValues(10, 1)
    assert live_value == [999]
