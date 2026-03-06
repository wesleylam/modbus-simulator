"""
Tests for core/store.py — RegisterStore and Register.
"""
import asyncio
import pytest

from core.store import Register, RegisterStore
from tests.conftest import make_register, make_store


# ── Register.to_dict ──────────────────────────────────────────────────────────

class TestRegisterToDict:
    def test_contains_all_keys(self):
        reg = make_register(address=10, reg_type="holding", name="speed", value=42, writable=True)
        d = reg.to_dict()
        assert set(d.keys()) == {"address", "type", "name", "value", "writable", "last_changed"}

    def test_values_match(self):
        reg = make_register(address=5, reg_type="coil", name="enable", value=1, writable=False)
        d = reg.to_dict()
        assert d["address"] == 5
        assert d["type"] == "coil"
        assert d["name"] == "enable"
        assert d["value"] == 1
        assert d["writable"] is False


# ── RegisterStore.load ────────────────────────────────────────────────────────

class TestLoad:
    def test_replaces_existing_data(self):
        store = make_store()
        assert len(store.all()) == 5
        store.load([make_register(99, "holding", "new", 0, True)])
        assert len(store.all()) == 1
        assert store.get(99) is not None

    def test_keyed_by_address(self):
        store = RegisterStore()
        store.load([make_register(7), make_register(8)])
        assert store.get(7) is not None
        assert store.get(8) is not None

    def test_empty_load_clears_store(self, store):
        # load() does NOT guard against empty — that's csv_loader's job
        store.load([])
        assert store.all() == []


# ── RegisterStore.get / all / is_writable ─────────────────────────────────────

class TestReadMethods:
    def test_get_existing(self, store):
        reg = store.get(1)
        assert reg is not None
        assert reg.name == "pump_speed"

    def test_get_missing_returns_none(self, store):
        assert store.get(999) is None

    def test_all_returns_list(self, store):
        assert len(store.all()) == 5

    def test_is_writable_true(self, store):
        assert store.is_writable(1) is True

    def test_is_writable_false(self, store):
        # address 3 = inlet_pressure, writable=False
        assert store.is_writable(3) is False

    def test_is_writable_missing_returns_false(self, store):
        assert store.is_writable(999) is False


# ── RegisterStore.set (async) ─────────────────────────────────────────────────

class TestAsyncSet:
    @pytest.mark.asyncio
    async def test_updates_value(self, store):
        await store.set(1, 150)
        assert store.get(1).value == 150

    @pytest.mark.asyncio
    async def test_returns_old_and_new(self, store):
        old, new = await store.set(2, 999)
        assert old == 200
        assert new == 999

    @pytest.mark.asyncio
    async def test_raises_on_missing_address(self, store):
        with pytest.raises(KeyError):
            await store.set(999, 0)

    @pytest.mark.asyncio
    async def test_updates_last_changed(self, store):
        before = store.get(1).last_changed
        await asyncio.sleep(0.01)
        await store.set(1, 50)
        assert store.get(1).last_changed > before

    @pytest.mark.asyncio
    async def test_fires_callbacks(self, store):
        events = []
        async def cb(addr, old, new, source, ip):
            events.append((addr, old, new, source))
        store.register_change_callback(cb)
        await store.set(1, 77, source="api")
        assert events == [(1, 0, 77, "api")]

    @pytest.mark.asyncio
    async def test_fires_multiple_callbacks(self, store):
        counts = [0, 0]
        async def cb1(*_): counts[0] += 1
        async def cb2(*_): counts[1] += 1
        store.register_change_callback(cb1)
        store.register_change_callback(cb2)
        await store.set(1, 1)
        assert counts == [1, 1]


# ── RegisterStore.set_sync ────────────────────────────────────────────────────

class TestSetSync:
    def test_updates_value(self, store):
        store.set_sync(1, 42)
        assert store.get(1).value == 42

    def test_returns_old_and_new(self, store):
        old, new = store.set_sync(2, 500)
        assert old == 200
        assert new == 500

    def test_missing_address_returns_none_tuple(self, store):
        result = store.set_sync(999, 0)
        assert result == (None, None)


# ── RegisterStore.add ─────────────────────────────────────────────────────────

class TestAdd:
    def test_adds_new_register(self, store):
        reg = make_register(100, "holding", "new_reg", 0, True)
        store.add(reg)
        assert store.get(100) is not None

    def test_raises_on_duplicate_address(self, store):
        with pytest.raises(ValueError, match="already exists"):
            store.add(make_register(1))  # address 1 already in store

    def test_count_increases(self, store):
        before = len(store.all())
        store.add(make_register(50))
        assert len(store.all()) == before + 1


# ── RegisterStore.remove ──────────────────────────────────────────────────────

class TestRemove:
    def test_removes_existing(self, store):
        assert store.remove(1) is True
        assert store.get(1) is None

    def test_returns_false_for_missing(self, store):
        assert store.remove(999) is False

    def test_count_decreases(self, store):
        before = len(store.all())
        store.remove(1)
        assert len(store.all()) == before - 1


# ── RegisterStore.edit_meta ───────────────────────────────────────────────────

class TestEditMeta:
    def test_edit_name(self, store):
        store.edit_meta(1, name="new_name")
        assert store.get(1).name == "new_name"

    def test_edit_type(self, store):
        store.edit_meta(1, reg_type="coil")
        assert store.get(1).reg_type == "coil"

    def test_edit_writable(self, store):
        store.edit_meta(3, writable=True)
        assert store.get(3).writable is True

    def test_partial_edit_preserves_others(self, store):
        original = store.get(1)
        original_type = original.reg_type
        store.edit_meta(1, name="changed")
        assert store.get(1).reg_type == original_type

    def test_returns_none_for_missing(self, store):
        assert store.edit_meta(999, name="x") is None

    def test_returns_register_on_success(self, store):
        result = store.edit_meta(1, name="updated")
        assert isinstance(result, Register)


# ── RegisterStore.get_values_by_type ─────────────────────────────────────────

class TestGetValuesByType:
    def test_returns_only_matching_type(self, store):
        vals = store.get_values_by_type("holding")
        assert set(vals.keys()) == {1, 2}  # pump_speed, setpoint_temp

    def test_returns_empty_for_unknown_type(self, store):
        assert store.get_values_by_type("unknown") == {}

    def test_values_are_correct(self, store):
        vals = store.get_values_by_type("holding")
        assert vals[2] == 200  # setpoint_temp initial value


# ── unit_id ───────────────────────────────────────────────────────────────────

class TestUnitId:
    def test_default_unit_id(self):
        store = RegisterStore()
        assert store.unit_id == 1

    def test_set_unit_id(self):
        store = RegisterStore()
        store.unit_id = 42
        assert store.unit_id == 42
