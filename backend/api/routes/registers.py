from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Any

from core.store import RegisterStore, Register
from core.events import event_bus, RegisterChangeEvent

router = APIRouter()

VALID_TYPES = {"coil", "discrete", "holding", "input"}

# ── Dependency ────────────────────────────────────────────────────────────────

def get_store(request: Request) -> RegisterStore:
    return request.app.state.store


# ── Schemas ───────────────────────────────────────────────────────────────────

class UpdateValueBody(BaseModel):
    value: int


class UpdateMetaBody(BaseModel):
    name: Optional[str] = None
    reg_type: Optional[str] = None
    writable: Optional[bool] = None


class CreateBody(BaseModel):
    address: int
    name: str
    reg_type: str       # frontend sends as "reg_type" after fix below
    value: int = 0
    writable: bool = True

    @model_validator(mode="before")
    @classmethod
    def remap_type(cls, data: Any) -> Any:
        # Accept both "type" (JSON from frontend) and "reg_type"
        if isinstance(data, dict) and "type" in data and "reg_type" not in data:
            data = dict(data)
            data["reg_type"] = data.pop("type")
        return data


class UpdateMetaBodyIn(BaseModel):
    name: Optional[str] = None
    reg_type: Optional[str] = None
    writable: Optional[bool] = None

    @model_validator(mode="before")
    @classmethod
    def remap_type(cls, data: Any) -> Any:
        if isinstance(data, dict) and "type" in data and "reg_type" not in data:
            data = dict(data)
            data["reg_type"] = data.pop("type")
        return data


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/")
async def list_registers(request: Request, store: RegisterStore = Depends(get_store)):
    return [r.to_dict() for r in store.all()]


@router.get("/{address}")
async def get_register(address: int, request: Request, store: RegisterStore = Depends(get_store)):
    reg = store.get(address)
    if reg is None:
        raise HTTPException(status_code=404, detail=f"Register {address} not found")
    return reg.to_dict()


@router.post("/")
async def create_register(body: CreateBody, request: Request, store: RegisterStore = Depends(get_store)):
    if body.reg_type not in VALID_TYPES:
        raise HTTPException(status_code=422, detail=f"type must be one of {VALID_TYPES}")
    try:
        reg = Register(
            address=body.address,
            reg_type=body.reg_type,
            name=body.name,
            value=body.value,
            writable=body.writable,
        )
        store.add(reg)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    await event_bus.put(RegisterChangeEvent(
        address=body.address, old_value=None, new_value=body.value,
        source="api", client_ip=None, event_type="add",
    ))
    return reg.to_dict()


@router.patch("/{address}/value")
async def update_value(
    address: int, body: UpdateValueBody,
    request: Request, store: RegisterStore = Depends(get_store),
):
    reg = store.get(address)
    if reg is None:
        raise HTTPException(status_code=404, detail=f"Register {address} not found")
    if not reg.writable:
        raise HTTPException(status_code=403, detail=f"Register {address} is read-only")
    old_value, new_value = await store.set(address, body.value, source="api")
    await event_bus.put(RegisterChangeEvent(
        address=address, old_value=old_value, new_value=new_value, source="api", client_ip=None,
    ))
    return {"address": address, "old_value": old_value, "new_value": new_value}


@router.patch("/{address}")
async def update_register(
    address: int, body: UpdateValueBody,
    request: Request, store: RegisterStore = Depends(get_store),
):
    reg = store.get(address)
    if reg is None:
        raise HTTPException(status_code=404, detail=f"Register {address} not found")
    if not reg.writable:
        raise HTTPException(status_code=403, detail=f"Register {address} is read-only")
    old_value, new_value = await store.set(address, body.value, source="api")
    await event_bus.put(RegisterChangeEvent(
        address=address, old_value=old_value, new_value=new_value, source="api", client_ip=None,
    ))
    return {"address": address, "old_value": old_value, "new_value": new_value}


@router.put("/{address}/meta")
async def update_meta(
    address: int, body: UpdateMetaBodyIn,
    request: Request, store: RegisterStore = Depends(get_store),
):
    if body.reg_type is not None and body.reg_type not in VALID_TYPES:
        raise HTTPException(status_code=422, detail=f"type must be one of {VALID_TYPES}")
    reg = store.edit_meta(address, name=body.name, reg_type=body.reg_type, writable=body.writable)
    if reg is None:
        raise HTTPException(status_code=404, detail=f"Register {address} not found")
    await event_bus.put(RegisterChangeEvent(
        address=address, old_value=None, new_value=None, source="api", client_ip=None, event_type="meta",
    ))
    return reg.to_dict()


@router.delete("/{address}")
async def delete_register(address: int, request: Request, store: RegisterStore = Depends(get_store)):
    removed = store.remove(address)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Register {address} not found")
    await event_bus.put(RegisterChangeEvent(
        address=address, old_value=None, new_value=None, source="api", client_ip=None, event_type="remove",
    ))
    return {"deleted": address}
