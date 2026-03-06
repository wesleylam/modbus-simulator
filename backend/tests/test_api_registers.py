"""
Tests for api/routes/registers.py — all CRUD endpoints.
"""
import pytest
from tests.conftest import make_register, make_store


# ── GET /registers ────────────────────────────────────────────────────────────

class TestListRegisters:
    @pytest.mark.asyncio
    async def test_returns_all_registers(self, client):
        r = await client.get("/registers/")
        assert r.status_code == 200
        assert len(r.json()) == 5

    @pytest.mark.asyncio
    async def test_response_shape(self, client):
        r = await client.get("/registers/")
        reg = r.json()[0]
        assert {"address", "type", "name", "value", "writable", "last_changed"} <= set(reg.keys())

    @pytest.mark.asyncio
    async def test_empty_store_returns_empty_list(self, empty_store, app):
        from httpx import AsyncClient, ASGITransport
        from api.app import create_app
        empty_app = create_app(empty_store)
        async with AsyncClient(transport=ASGITransport(app=empty_app), base_url="http://test") as c:
            r = await c.get("/registers/")
        assert r.status_code == 200
        assert r.json() == []


# ── GET /registers/{address} ──────────────────────────────────────────────────

class TestGetRegister:
    @pytest.mark.asyncio
    async def test_returns_correct_register(self, client):
        r = await client.get("/registers/1")
        assert r.status_code == 200
        data = r.json()
        assert data["address"] == 1
        assert data["name"] == "pump_speed"

    @pytest.mark.asyncio
    async def test_404_for_missing(self, client):
        r = await client.get("/registers/999")
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_404_message_contains_address(self, client):
        r = await client.get("/registers/999")
        assert "999" in r.json()["detail"]


# ── POST /registers ───────────────────────────────────────────────────────────

class TestCreateRegister:
    @pytest.mark.asyncio
    async def test_creates_register(self, client):
        r = await client.post("/registers/", json={
            "address": 100, "type": "holding", "name": "new_reg", "value": 42, "writable": True
        })
        assert r.status_code == 200
        assert r.json()["address"] == 100

    @pytest.mark.asyncio
    async def test_register_persisted_in_store(self, client, store):
        await client.post("/registers/", json={
            "address": 100, "type": "holding", "name": "new_reg", "value": 42, "writable": True
        })
        assert store.get(100) is not None

    @pytest.mark.asyncio
    async def test_accepts_type_field(self, client):
        # Frontend sends "type", not "reg_type" — must be remapped
        r = await client.post("/registers/", json={
            "address": 101, "type": "coil", "name": "test_coil", "value": 0, "writable": True
        })
        assert r.status_code == 200
        assert r.json()["type"] == "coil"

    @pytest.mark.asyncio
    async def test_all_register_types_accepted(self, client):
        for i, reg_type in enumerate(["holding", "input", "coil", "discrete"], start=200):
            r = await client.post("/registers/", json={
                "address": i, "type": reg_type, "name": f"reg_{i}", "value": 0, "writable": True
            })
            assert r.status_code == 200, f"Failed for type {reg_type}"

    @pytest.mark.asyncio
    async def test_409_on_duplicate_address(self, client):
        r = await client.post("/registers/", json={
            "address": 1, "type": "holding", "name": "dup", "value": 0, "writable": True
        })
        assert r.status_code == 409

    @pytest.mark.asyncio
    async def test_422_on_invalid_type(self, client):
        r = await client.post("/registers/", json={
            "address": 100, "type": "relay", "name": "bad", "value": 0, "writable": True
        })
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_default_value_is_zero(self, client, store):
        await client.post("/registers/", json={
            "address": 100, "type": "holding", "name": "no_val", "writable": True
        })
        assert store.get(100).value == 0

    @pytest.mark.asyncio
    async def test_default_writable_is_true(self, client, store):
        await client.post("/registers/", json={
            "address": 100, "type": "holding", "name": "no_access"
        })
        assert store.get(100).writable is True


# ── PATCH /registers/{address} ────────────────────────────────────────────────

class TestUpdateValue:
    @pytest.mark.asyncio
    async def test_updates_value(self, client, store):
        r = await client.patch("/registers/1", json={"value": 99})
        assert r.status_code == 200
        assert store.get(1).value == 99

    @pytest.mark.asyncio
    async def test_returns_old_and_new(self, client):
        r = await client.patch("/registers/2", json={"value": 500})
        data = r.json()
        assert data["old_value"] == 200
        assert data["new_value"] == 500

    @pytest.mark.asyncio
    async def test_404_for_missing_register(self, client):
        r = await client.patch("/registers/999", json={"value": 1})
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_403_for_read_only_register(self, client):
        # address 3 = inlet_pressure, read-only
        r = await client.patch("/registers/3", json={"value": 1})
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_403_message_mentions_read_only(self, client):
        r = await client.patch("/registers/3", json={"value": 1})
        assert "read-only" in r.json()["detail"].lower()


# ── PUT /registers/{address}/meta ─────────────────────────────────────────────

class TestUpdateMeta:
    @pytest.mark.asyncio
    async def test_updates_name(self, client, store):
        r = await client.put("/registers/1/meta", json={"name": "new_name"})
        assert r.status_code == 200
        assert store.get(1).name == "new_name"

    @pytest.mark.asyncio
    async def test_updates_type(self, client, store):
        r = await client.put("/registers/1/meta", json={"type": "coil"})
        assert r.status_code == 200
        assert store.get(1).reg_type == "coil"

    @pytest.mark.asyncio
    async def test_updates_writable(self, client, store):
        r = await client.put("/registers/3/meta", json={"writable": True})
        assert r.status_code == 200
        assert store.get(3).writable is True

    @pytest.mark.asyncio
    async def test_partial_update_preserves_other_fields(self, client, store):
        original_type = store.get(1).reg_type
        await client.put("/registers/1/meta", json={"name": "only_name_changed"})
        assert store.get(1).reg_type == original_type

    @pytest.mark.asyncio
    async def test_accepts_type_field_alias(self, client, store):
        r = await client.put("/registers/1/meta", json={"type": "input"})
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_404_for_missing_register(self, client):
        r = await client.put("/registers/999/meta", json={"name": "x"})
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_422_for_invalid_type(self, client):
        r = await client.put("/registers/1/meta", json={"type": "relay"})
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_value_unchanged_after_meta_edit(self, client, store):
        original_value = store.get(2).value
        await client.put("/registers/2/meta", json={"name": "renamed"})
        assert store.get(2).value == original_value


# ── DELETE /registers/{address} ───────────────────────────────────────────────

class TestDeleteRegister:
    @pytest.mark.asyncio
    async def test_deletes_register(self, client, store):
        r = await client.delete("/registers/1")
        assert r.status_code == 200
        assert store.get(1) is None

    @pytest.mark.asyncio
    async def test_returns_deleted_address(self, client):
        r = await client.delete("/registers/1")
        assert r.json()["deleted"] == 1

    @pytest.mark.asyncio
    async def test_404_for_missing_register(self, client):
        r = await client.delete("/registers/999")
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_double_delete_returns_404(self, client):
        await client.delete("/registers/1")
        r = await client.delete("/registers/1")
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_store_count_decreases(self, client, store):
        before = len(store.all())
        await client.delete("/registers/1")
        assert len(store.all()) == before - 1
