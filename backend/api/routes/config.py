import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Request
import tempfile
from pydantic import BaseModel, Field

from core.csv_loader import load_csv, CSVValidationError
from core.events import event_bus, RegisterChangeEvent
from modbus import server as modbus_server

router = APIRouter()

CSV_PATH = os.environ.get("CSV_PATH", "/app/registers.csv")


class ReloadResponse(BaseModel):
    message: str
    register_count: int


class UnitIdBody(BaseModel):
    unit_id: int = Field(..., ge=1, le=247)


class UnitIdResponse(BaseModel):
    unit_id: int


@router.get("/unit-id", response_model=UnitIdResponse)
async def get_unit_id(request: Request):
    """Get the current Modbus device unit ID (slave address)."""
    return UnitIdResponse(unit_id=request.app.state.store.unit_id)


@router.put("/unit-id", response_model=UnitIdResponse)
async def set_unit_id(body: UnitIdBody, request: Request):
    """
    Update the Modbus device unit ID (1–247) at runtime.
    Takes effect immediately — no server restart needed.
    """
    store = request.app.state.store
    old_id = store.unit_id
    store.unit_id = body.unit_id

    # Notify dashboard clients via WebSocket
    await event_bus.put(RegisterChangeEvent(
        address=0, old_value=old_id, new_value=body.unit_id,
        source="api", client_ip=None, event_type="unit_id_changed",
    ))

    # Ensure the running Modbus context (if any) accepts the new unit id
    try:
        modbus_server.update_unit_id(body.unit_id)
    except Exception:
        pass

    return UnitIdResponse(unit_id=store.unit_id)


@router.post("/reload", response_model=ReloadResponse)
async def reload_config(request: Request):
    """Hot-reload the register map from the mounted CSV file."""
    store = request.app.state.store
    try:
        registers = load_csv(CSV_PATH)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"CSV not found at {CSV_PATH}")
    except CSVValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    store.load(registers)
    return ReloadResponse(message="Register map reloaded successfully", register_count=len(registers))


@router.post("/upload", response_model=ReloadResponse)
async def upload_config(request: Request, file: UploadFile = File(...)):
    """Upload a new CSV file and immediately load it."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    contents = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    store = request.app.state.store
    try:
        registers = load_csv(tmp_path)
    except CSVValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    csv_dir = os.path.dirname(CSV_PATH) or "."
    os.makedirs(csv_dir, exist_ok=True)
    with open(CSV_PATH, "wb") as f:
        f.write(contents)

    store.load(registers)
    return ReloadResponse(message="CSV uploaded and loaded successfully", register_count=len(registers))
