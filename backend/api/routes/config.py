import os
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from core.csv_loader import load_csv, CSVValidationError

router = APIRouter()

CSV_PATH = os.environ.get("CSV_PATH", "/app/registers.csv")


class ReloadResponse(BaseModel):
    message: str
    register_count: int


@router.post("/reload", response_model=ReloadResponse)
async def reload_config(request=None):
    """
    Hot-reload the register map from the mounted CSV file.
    Replaces the in-memory store without restarting the server.
    Existing values for preserved addresses are overwritten with CSV defaults.
    """
    store = request.app.state.store
    try:
        registers = load_csv(CSV_PATH)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"CSV not found at {CSV_PATH}")
    except CSVValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    store.load(registers)
    return ReloadResponse(
        message="Register map reloaded successfully",
        register_count=len(registers),
    )


@router.post("/upload", response_model=ReloadResponse)
async def upload_config(request=None, file: UploadFile = File(...)):
    """
    Upload a new CSV file and immediately load it into the register store.
    Also saves it to the configured CSV_PATH for persistence across reloads.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    contents = await file.read()
    tmp_path = "/tmp/uploaded_registers.csv"
    with open(tmp_path, "wb") as f:
        f.write(contents)

    store = request.app.state.store
    try:
        registers = load_csv(tmp_path)
    except CSVValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Save to the configured path and load
    with open(CSV_PATH, "wb") as f:
        f.write(contents)

    store.load(registers)
    return ReloadResponse(
        message="CSV uploaded and loaded successfully",
        register_count=len(registers),
    )
