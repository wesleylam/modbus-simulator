"""
Tests for core/events.py — RegisterChangeEvent.
"""
import time
import pytest

from core.events import RegisterChangeEvent


class TestRegisterChangeEvent:
    def test_default_event_type_is_update(self):
        evt = RegisterChangeEvent(1, 0, 1, "api", None)
        assert evt.event_type == "update"

    def test_custom_event_type(self):
        evt = RegisterChangeEvent(1, None, 0, "api", None, event_type="add")
        assert evt.event_type == "add"

    def test_timestamp_auto_set(self):
        before = time.time()
        evt = RegisterChangeEvent(1, 0, 1, "api", None)
        assert evt.timestamp >= before

    def test_explicit_timestamp_preserved(self):
        evt = RegisterChangeEvent(1, 0, 1, "api", None, timestamp=12345.0)
        assert evt.timestamp == 12345.0

    def test_to_dict_contains_all_keys(self):
        evt = RegisterChangeEvent(1, 0, 100, "modbus", "192.168.1.1")
        d = evt.to_dict()
        assert set(d.keys()) == {"type", "address", "old_value", "new_value", "source", "client_ip", "timestamp"}

    def test_to_dict_type_reflects_event_type(self):
        evt = RegisterChangeEvent(1, 0, 1, "api", None, event_type="remove")
        assert evt.to_dict()["type"] == "remove"

    def test_to_dict_values_correct(self):
        evt = RegisterChangeEvent(5, 10, 20, "modbus", "10.0.0.1", timestamp=999.0)
        d = evt.to_dict()
        assert d["address"] == 5
        assert d["old_value"] == 10
        assert d["new_value"] == 20
        assert d["source"] == "modbus"
        assert d["client_ip"] == "10.0.0.1"
        assert d["timestamp"] == 999.0

    def test_none_values_for_add_event(self):
        evt = RegisterChangeEvent(1, None, 42, "api", None, event_type="add")
        d = evt.to_dict()
        assert d["old_value"] is None
        assert d["new_value"] == 42

    def test_none_values_for_remove_event(self):
        evt = RegisterChangeEvent(1, None, None, "api", None, event_type="remove")
        d = evt.to_dict()
        assert d["old_value"] is None
        assert d["new_value"] is None
