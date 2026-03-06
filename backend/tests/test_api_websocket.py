"""
Tests for /status endpoint and WebSocket snapshot + live updates.
"""
import json
import asyncio
import pytest
from httpx_ws import aconnect_ws


# ── GET /status ───────────────────────────────────────────────────────────────

class TestStatus:
    @pytest.mark.asyncio
    async def test_returns_ok(self, client):
        r = await client.get("/status")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    @pytest.mark.asyncio
    async def test_returns_register_count(self, client):
        r = await client.get("/status")
        assert r.json()["register_count"] == 5

    @pytest.mark.asyncio
    async def test_returns_ws_connections(self, client):
        r = await client.get("/status")
        assert "ws_connections" in r.json()


# ── WebSocket ─────────────────────────────────────────────────────────────────

class TestWebSocket:
    @pytest.mark.asyncio
    async def test_snapshot_on_connect(self, app):
        """Client should receive a snapshot message immediately on connect."""
        async with aconnect_ws("/ws", app) as ws:
            msg = json.loads(await ws.receive_text())
            assert msg["type"] == "snapshot"
            assert "registers" in msg
            assert len(msg["registers"]) == 5

    @pytest.mark.asyncio
    async def test_snapshot_contains_all_fields(self, app):
        async with aconnect_ws("/ws", app) as ws:
            msg = json.loads(await ws.receive_text())
            reg = msg["registers"][0]
            assert {"address", "type", "name", "value", "writable", "last_changed"} <= set(reg.keys())

    @pytest.mark.asyncio
    async def test_receives_update_on_register_change(self, app, client):
        """After a PATCH, the WebSocket client should receive an update event."""
        async with aconnect_ws("/ws", app) as ws:
            # Consume snapshot
            await ws.receive_text()

            # Trigger a value change via REST
            await client.patch("/registers/1", json={"value": 123})

            # Should receive update
            msg = json.loads(await ws.receive_text())
            assert msg["type"] == "update"
            assert msg["address"] == 1
            assert msg["new_value"] == 123

    @pytest.mark.asyncio
    async def test_receives_add_event(self, app, client):
        async with aconnect_ws("/ws", app) as ws:
            await ws.receive_text()  # snapshot
            await client.post("/registers/", json={
                "address": 100, "type": "holding", "name": "new", "value": 0, "writable": True
            })
            msg = json.loads(await ws.receive_text())
            assert msg["type"] == "add"
            assert msg["address"] == 100

    @pytest.mark.asyncio
    async def test_receives_remove_event(self, app, client):
        async with aconnect_ws("/ws", app) as ws:
            await ws.receive_text()  # snapshot
            await client.delete("/registers/1")
            msg = json.loads(await ws.receive_text())
            assert msg["type"] == "remove"
            assert msg["address"] == 1

    @pytest.mark.asyncio
    async def test_receives_unit_id_changed_event(self, app, client):
        async with aconnect_ws("/ws", app) as ws:
            await ws.receive_text()  # snapshot
            await client.put("/config/unit-id", json={"unit_id": 5})
            msg = json.loads(await ws.receive_text())
            assert msg["type"] == "unit_id_changed"
            assert msg["new_value"] == 5

    @pytest.mark.asyncio
    async def test_multiple_clients_all_receive_update(self, app, client):
        """All connected clients should receive broadcast events."""
        async with aconnect_ws("/ws", app) as ws1, aconnect_ws("/ws", app) as ws2:
            await ws1.receive_text()
            await ws2.receive_text()

            await client.patch("/registers/1", json={"value": 77})

            msg1 = json.loads(await ws1.receive_text())
            msg2 = json.loads(await ws2.receive_text())
            assert msg1["new_value"] == 77
            assert msg2["new_value"] == 77
