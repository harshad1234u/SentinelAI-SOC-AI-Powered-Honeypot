from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
import uuid
import json
from app.websocket.manager import ws_manager
from app.core.security import verify_token
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

async def get_ws_user(token: str = Query(...)):
    payload = verify_token(token)
    if not payload:
        return None
    return payload

@router.websocket("/ws/attacks")
async def websocket_attacks(websocket: WebSocket, token: str = Query(None)):
    if not token:
        await websocket.close(code=1008)
        return
        
    user = verify_token(token)
    if not user:
        await websocket.close(code=1008)
        return

    client_id = str(uuid.uuid4())
    await ws_manager.connect(websocket, client_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "subscribe":
                    logger.info(f"Client {client_id} subscribed with filters: {message.get('filters')}")
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(client_id)
