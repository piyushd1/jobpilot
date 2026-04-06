from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import asyncio

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/{campaign_id}/stream")
async def websocket_endpoint(websocket: WebSocket, campaign_id: str):
    await manager.connect(websocket)
    try:
        # Simulated live stream from Temporal/Redis PubSub
        await websocket.send_text(json.dumps({
            "type": "UPDATE",
            "data": {"phase": "INITIALIZATION", "status": "OK", "detail": "Validating candidate payload."}
        }))
        await asyncio.sleep(2)
        await websocket.send_text(json.dumps({
            "type": "UPDATE",
            "data": {"phase": "DISCOVERY", "status": "IN_PROGRESS", "detail": "Querying Naukri & LinkedIn platforms."}
        }))
        await asyncio.sleep(3)
        await websocket.send_text(json.dumps({
            "type": "UPDATE",
            "data": {"phase": "COMPLETED", "status": "OK", "detail": "Shortlist ready for review."}
        }))
        
        while True:
            # Maintain open socket for future events
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
