import pytest
from httpx import AsyncClient, ASGITransport
from modbus import server as modbus_server
from api.app import create_app
from core.store import RegisterStore


@pytest.mark.asyncio
async def test_api_updates_modbus_unit_id():
    store = RegisterStore()
    app = create_app(store)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        # initial value should be set into modbus_server
        assert modbus_server.get_current_unit_id() == store.unit_id

        r = await c.put("/config/unit-id", json={"unit_id": 5})
        assert r.status_code == 200
        assert modbus_server.get_current_unit_id() == store.unit_id