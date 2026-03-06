import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.store import RegisterStore
from api.routes.registers import router as registers_router
from api.routes.config import router as config_router
from api.websocket import ws_router, broadcast_loop, get_connection_count

logger = logging.getLogger(__name__)


def create_app(store: RegisterStore) -> FastAPI:
    app = FastAPI(
        title="Modbus Simulator API",
        description="REST + WebSocket interface for the Modbus TCP register simulator",
        version="1.0.0",
    )

    # Allow the React dashboard (served separately in dev) to call the API
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Attach store to app state so routes can access it via request.app.state.store
    app.state.store = store

    # Mount routers
    app.include_router(registers_router, prefix="/registers", tags=["Registers"])
    app.include_router(config_router, prefix="/config", tags=["Config"])
    app.include_router(ws_router, tags=["WebSocket"])

    @app.on_event("startup")
    async def startup():
        logger.info("Starting WebSocket broadcast loop")
        asyncio.create_task(broadcast_loop())

    @app.get("/status", tags=["Health"])
    async def status():
        return {
            "status": "ok",
            "register_count": len(store.all()),
            "ws_connections": get_connection_count(),
        }

    return app
