from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from core.store import RegisterStore
from core.events import event_bus, RegisterChangeEvent

router = APIRouter()


# ── Dependency ────────────────────────────────────────────────────────────────

def get_store(request) -> RegisterStore:
    return request.app.state.store


# ── Schemas ───────────────────────────────────────────────────────────────────

class UpdateBody(BaseModel):
    value: int | bool


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/")
async def list_registers(request=None, store: RegisterStore = Depends(get_store)):
    """Return all registers with their current live values."""
    return [r.to_dict() for r in store.all()]


@router.get("/{address}")
async def get_register(address: int, request=None, store: RegisterStore = Depends(get_store)):
    """Return a single register by address."""
    reg = store.get(address)
    if reg is None:
        raise HTTPException(status_code=404, detail=f"Register {address} not found")
    return reg.to_dict()


@router.patch("/{address}")
async def update_register(
    address: int,
    body: UpdateBody,
    request=None,
    store: RegisterStore = Depends(get_store),
):
    """
    Update a register's value from the dashboard.
    Only writable (RW) registers can be updated.
    """
    reg = store.get(address)
    if reg is None:
        raise HTTPException(status_code=404, detail=f"Register {address} not found")
    if not reg.writable:
        raise HTTPException(status_code=403, detail=f"Register {address} is read-only")

    old_value, new_value = await store.set(address, body.value, source="api")

    # Emit change event so WebSocket clients get notified
    evt = RegisterChangeEvent(
        address=address,
        old_value=old_value,
        new_value=new_value,
        source="api",
        client_ip=None,
    )
    await event_bus.put(evt)

    return {"address": address, "old_value": old_value, "new_value": new_value}
