import asyncio
import logging
import os
import threading

import uvicorn

from core.store import RegisterStore
from core.csv_loader import load_csv, CSVValidationError
from modbus.server import start_modbus_server
from api.app import create_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

CSV_PATH   = os.environ.get("CSV_PATH",    "/app/registers.csv")
MODBUS_HOST = os.environ.get("MODBUS_HOST", "0.0.0.0")
MODBUS_PORT = int(os.environ.get("MODBUS_PORT", "502"))
API_HOST    = os.environ.get("API_HOST",   "0.0.0.0")
API_PORT    = int(os.environ.get("API_PORT",   "8000"))


def main():
    # 1. Load registers from CSV
    logger.info(f"Loading register map from {CSV_PATH}")
    try:
        registers = load_csv(CSV_PATH)
    except (FileNotFoundError, CSVValidationError) as e:
        logger.error(f"Failed to load CSV: {e}")
        raise SystemExit(1)

    logger.info(f"Loaded {len(registers)} registers")

    # 2. Populate store
    store = RegisterStore()
    store.load(registers)

    # 3. Start Modbus TCP server in a background daemon thread
    modbus_thread = threading.Thread(
        target=start_modbus_server,
        args=(store, MODBUS_HOST, MODBUS_PORT),
        daemon=True,
        name="modbus-server",
    )
    modbus_thread.start()
    logger.info(f"Modbus TCP server starting on {MODBUS_HOST}:{MODBUS_PORT}")

    # 4. Build and run FastAPI app (blocks until shutdown)
    app = create_app(store)
    logger.info(f"API server starting on {API_HOST}:{API_PORT}")
    uvicorn.run(app, host=API_HOST, port=API_PORT, log_level="info")


if __name__ == "__main__":
    main()
