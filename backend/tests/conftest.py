"""
Shared fixtures for the Modbus Simulator test suite.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from core.store import Register, RegisterStore
from api.app import create_app


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_register(address=1, reg_type="holding", name="test_reg", value=0, writable=True):
    return Register(address=address, reg_type=reg_type, name=name, value=value, writable=writable)


def make_store(*registers) -> RegisterStore:
    store = RegisterStore()
    regs = list(registers) if registers else [
        make_register(1,  "holding",  "pump_speed",    0,   True),
        make_register(2,  "holding",  "setpoint_temp", 200, True),
        make_register(3,  "input",    "inlet_pressure", 0,  False),
        make_register(4,  "coil",     "pump_enable",   0,   True),
        make_register(5,  "discrete", "fault_active",  0,   False),
    ]
    store.load(regs)
    return store


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def store() -> RegisterStore:
    return make_store()


@pytest.fixture
def empty_store() -> RegisterStore:
    return RegisterStore()


@pytest_asyncio.fixture
async def app(store):
    fastapi_app = create_app(store)
    async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def client(store):
    app = create_app(store)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
