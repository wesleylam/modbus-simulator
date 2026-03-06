import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.events import event_bus

logger = logging.getLogger(__name__)
ws_router = APIRouter()

# Active WebSocket connections
_connections: set[WebSocket] = set()


@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint — clients connect here to receive live register updates.

    On connect: sends a snapshot of all current register values.
    Ongoing: streams RegisterChangeEvent messages as JSON.

    Message format:
        {
            "type": "snapshot" | "update",
            "registers": [...],       # snapshot only
            "address": 1,             # update only
            "old_value": 0,           # update only
            "new_value": 100,         # update only
            "source": "modbus"|"api", # update only
            "client_ip": "...",       # update only (may be null)
            "timestamp": 1234567890.0
        }
    """
    await websocket.accept()
    _connections.add(websocket)
    logger.info(f"WebSocket client connected. Total: {len(_connections)}")

    try:
        # Send initial snapshot
        store = websocket.app.state.store
        snapshot = {
            "type": "snapshot",
            "registers": [r.to_dict() for r in store.all()],
        }
        await websocket.send_text(json.dumps(snapshot))

        # Keep connection alive — client messages are ignored (ping/pong handled by FastAPI)
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        pass
    finally:
        _connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(_connections)}")


async def broadcast_loop():
    """
    Background task: consumes events from the event bus and broadcasts
    them to all connected WebSocket clients. Runs for the lifetime of the app.
    """
    logger.info("WebSocket broadcast loop started")
    while True:
        try:
            evt = await event_bus.get()
            if not _connections:
                continue

            message = json.dumps(evt.to_dict())
            dead = set()

            for ws in list(_connections):
                try:
                    await ws.send_text(message)
                except Exception:
                    dead.add(ws)

            _connections.difference_update(dead)

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Broadcast loop error: {e}")


def get_connection_count() -> int:
    return len(_connections)
