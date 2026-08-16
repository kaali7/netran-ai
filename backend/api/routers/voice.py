"""
Netran AI — Stage 3 WebSocket Voice Streaming Router.
Bidirectional live Audio streaming handler.
"""

from fastapi import APIRouter, WebSocket, status

router = APIRouter(prefix="/voice", tags=["Voice Stream (WebSocket)"])


@router.websocket("/stream/{session_id}")
async def voice_stream(websocket: WebSocket, session_id: str):
    """Real-time audio streaming WebSocket endpoint for Stage 3 voice loop."""
    await websocket.accept()
    await websocket.send_json({
        "event": "ERROR",
        "message": "Voice streaming endpoint stub — WebSocket handler to be implemented."
    })
    await websocket.close(code=status.WS_1000_NORMAL_CLOSURE)
