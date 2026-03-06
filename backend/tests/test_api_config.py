"""
Tests for api/routes/config.py — unit ID, CSV reload, CSV upload.
"""
import pytest
from unittest.mock import patch, MagicMock

from core.store import Register
from core.csv_loader import CSVValidationError


VALID_CSV_BYTES = (
    b"address,type,name,value,access\n"
    b"10,holding,new_speed,0,RW\n"
    b"11,input,new_pressure,0,R\n"
)


# ── GET /config/unit-id ───────────────────────────────────────────────────────

class TestGetUnitId:
    @pytest.mark.asyncio
    async def test_returns_default_unit_id(self, client):
        r = await client.get("/config/unit-id")
        assert r.status_code == 200
        assert r.json()["unit_id"] == 1

    @pytest.mark.asyncio
    async def test_returns_updated_unit_id(self, client, store):
        store.unit_id = 42
        r = await client.get("/config/unit-id")
        assert r.json()["unit_id"] == 42


# ── PUT /config/unit-id ───────────────────────────────────────────────────────

class TestSetUnitId:
    @pytest.mark.asyncio
    async def test_updates_unit_id(self, client, store):
        r = await client.put("/config/unit-id", json={"unit_id": 5})
        assert r.status_code == 200
        assert store.unit_id == 5

    @pytest.mark.asyncio
    async def test_returns_new_unit_id(self, client):
        r = await client.put("/config/unit-id", json={"unit_id": 10})
        assert r.json()["unit_id"] == 10

    @pytest.mark.asyncio
    async def test_accepts_boundary_value_1(self, client):
        r = await client.put("/config/unit-id", json={"unit_id": 1})
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_accepts_boundary_value_247(self, client):
        r = await client.put("/config/unit-id", json={"unit_id": 247})
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_rejects_unit_id_zero(self, client):
        r = await client.put("/config/unit-id", json={"unit_id": 0})
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_rejects_unit_id_248(self, client):
        r = await client.put("/config/unit-id", json={"unit_id": 248})
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_rejects_negative_unit_id(self, client):
        r = await client.put("/config/unit-id", json={"unit_id": -1})
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_rejects_string_unit_id(self, client):
        r = await client.put("/config/unit-id", json={"unit_id": "abc"})
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_emits_ws_event(self, client):
        from core.events import event_bus
        # Drain any existing events
        while not event_bus.empty():
            event_bus.get_nowait()

        await client.put("/config/unit-id", json={"unit_id": 7})
        assert not event_bus.empty()
        evt = event_bus.get_nowait()
        assert evt.event_type == "unit_id_changed"
        assert evt.new_value == 7


# ── POST /config/reload ───────────────────────────────────────────────────────

class TestReloadConfig:
    @pytest.mark.asyncio
    async def test_reloads_registers_from_file(self, client, store, tmp_path):
        csv_path = tmp_path / "regs.csv"
        csv_path.write_bytes(VALID_CSV_BYTES)

        with patch("api.routes.config.CSV_PATH", str(csv_path)):
            r = await client.post("/config/reload")

        assert r.status_code == 200
        assert r.json()["register_count"] == 2
        assert store.get(10) is not None

    @pytest.mark.asyncio
    async def test_reload_replaces_old_registers(self, client, store, tmp_path):
        csv_path = tmp_path / "regs.csv"
        csv_path.write_bytes(VALID_CSV_BYTES)

        with patch("api.routes.config.CSV_PATH", str(csv_path)):
            await client.post("/config/reload")

        # Original registers (1–5) should be gone
        assert store.get(1) is None

    @pytest.mark.asyncio
    async def test_404_when_csv_not_found(self, client):
        with patch("api.routes.config.CSV_PATH", "/nonexistent/path.csv"):
            r = await client.post("/config/reload")
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_422_on_invalid_csv(self, client, tmp_path):
        bad_csv = tmp_path / "bad.csv"
        bad_csv.write_text("address,type\n1,holding\n")  # missing columns

        with patch("api.routes.config.CSV_PATH", str(bad_csv)):
            r = await client.post("/config/reload")
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_response_message(self, client, tmp_path):
        csv_path = tmp_path / "regs.csv"
        csv_path.write_bytes(VALID_CSV_BYTES)

        with patch("api.routes.config.CSV_PATH", str(csv_path)):
            r = await client.post("/config/reload")
        assert "reloaded" in r.json()["message"].lower()


# ── POST /config/upload ───────────────────────────────────────────────────────

class TestUploadConfig:
    @pytest.mark.asyncio
    async def test_upload_loads_registers(self, client, store, tmp_path):
        dest = tmp_path / "dest.csv"
        with patch("api.routes.config.CSV_PATH", str(dest)):
            r = await client.post(
                "/config/upload",
                files={"file": ("registers.csv", VALID_CSV_BYTES, "text/csv")},
            )
        assert r.status_code == 200
        assert store.get(10) is not None

    @pytest.mark.asyncio
    async def test_upload_replaces_old_registers(self, client, store, tmp_path):
        dest = tmp_path / "dest.csv"
        with patch("api.routes.config.CSV_PATH", str(dest)):
            await client.post(
                "/config/upload",
                files={"file": ("registers.csv", VALID_CSV_BYTES, "text/csv")},
            )
        assert store.get(1) is None  # original register gone

    @pytest.mark.asyncio
    async def test_upload_returns_register_count(self, client, tmp_path):
        dest = tmp_path / "dest.csv"
        with patch("api.routes.config.CSV_PATH", str(dest)):
            r = await client.post(
                "/config/upload",
                files={"file": ("registers.csv", VALID_CSV_BYTES, "text/csv")},
            )
        assert r.json()["register_count"] == 2

    @pytest.mark.asyncio
    async def test_rejects_non_csv_file(self, client):
        r = await client.post(
            "/config/upload",
            files={"file": ("registers.txt", b"some text", "text/plain")},
        )
        assert r.status_code == 400

    @pytest.mark.asyncio
    async def test_422_on_invalid_csv_content(self, client, tmp_path):
        dest = tmp_path / "dest.csv"
        bad_content = b"address,type\n1,holding\n"  # missing columns
        with patch("api.routes.config.CSV_PATH", str(dest)):
            r = await client.post(
                "/config/upload",
                files={"file": ("registers.csv", bad_content, "text/csv")},
            )
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_saves_file_to_csv_path(self, client, tmp_path):
        dest = tmp_path / "dest.csv"
        with patch("api.routes.config.CSV_PATH", str(dest)):
            await client.post(
                "/config/upload",
                files={"file": ("registers.csv", VALID_CSV_BYTES, "text/csv")},
            )
        assert dest.exists()
        assert dest.read_bytes() == VALID_CSV_BYTES
