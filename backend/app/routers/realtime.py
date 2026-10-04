import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.care import Notification
from app.models.user import User

router = APIRouter(tags=["Realtime"])
ALGORITHM = "HS256"


def _user_from_token(token: str):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        return None


@router.websocket("/ws/notifications")
async def notification_stream(websocket: WebSocket):
    user_id = _user_from_token(websocket.query_params.get("token", ""))
    if not user_id:
        await websocket.close(code=4401)
        return
    db = SessionLocal()
    try:
        user = db.get(User, user_id)
        if not user or not user.is_active:
            await websocket.close(code=4401)
            return
        await websocket.accept()
        last_count = -1
        while True:
            db.expire_all()
            unread = db.query(Notification).filter(Notification.user_id == user_id, Notification.is_read == False).count()
            if unread != last_count:
                await websocket.send_json({"type": "notification_count", "unread": unread})
                last_count = unread
            await asyncio.sleep(4)
    except WebSocketDisconnect:
        pass
    finally:
        db.close()
