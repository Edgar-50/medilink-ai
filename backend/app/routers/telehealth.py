
import secrets
from datetime import datetime, timezone
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from pydantic import BaseModel
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import ALGORITHM, get_current_user
from app.models.user import User

router=APIRouter(prefix="/api/v1/telehealth",tags=["Telehealth"])
rooms:dict[str,dict]={}
connections:dict[str,list[WebSocket]]=defaultdict(list)

class RoomResponse(BaseModel):
    room_id:str; join_code:str; created_at:str; transport:str; secure_media:bool

@router.post("/rooms",response_model=RoomResponse)
def create_room(current_user:User=Depends(get_current_user)):
    rid=f"ml-{secrets.token_hex(4)}"; code=secrets.token_urlsafe(8)
    rooms[rid]={"join_code":code,"creator":current_user.id,"created_at":datetime.now(timezone.utc).isoformat()}
    return RoomResponse(room_id=rid,join_code=code,created_at=rooms[rid]["created_at"],transport="WebRTC",secure_media=True)

@router.get("/rooms/{room_id}")
def room_status(room_id:str,join_code:str,current_user:User=Depends(get_current_user)):
    room=rooms.get(room_id)
    if not room or room["join_code"]!=join_code: raise HTTPException(status_code=404,detail="Room not found")
    return {"room_id":room_id,"participants":len(connections.get(room_id,[])),"ready":True}

def _ws_user(token:str):
    try:
        payload=jwt.decode(token,settings.secret_key,algorithms=[ALGORITHM]); uid=int(payload.get("sub"))
    except (JWTError,TypeError,ValueError): return None
    db=SessionLocal()
    try:
        u=db.get(User,uid)
        return {"id":u.id,"name":u.full_name,"role":u.role.value} if u and u.is_active else None
    finally: db.close()

@router.websocket("/ws/{room_id}")
async def signalling(websocket:WebSocket,room_id:str):
    token=websocket.query_params.get("token",""); code=websocket.query_params.get("join_code","")
    user=_ws_user(token); room=rooms.get(room_id)
    if not user or not room or room["join_code"]!=code:
        await websocket.close(code=4401); return
    if len(connections[room_id])>=2:
        await websocket.close(code=4409); return
    await websocket.accept(); connections[room_id].append(websocket)
    await websocket.send_json({"type":"presence","event":"joined","user":user,"participants":len(connections[room_id])})
    for peer in list(connections[room_id]):
        if peer is not websocket:
            try: await peer.send_json({"type":"presence","event":"peer_joined","user":user,"participants":len(connections[room_id])})
            except Exception: pass
    try:
        while True:
            data=await websocket.receive_json()
            if data.get("type") not in {"offer","answer","ice","hangup"}: continue
            for peer in list(connections[room_id]):
                if peer is not websocket:
                    try: await peer.send_json(data)
                    except Exception: pass
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in connections.get(room_id,[]): connections[room_id].remove(websocket)
        for peer in list(connections.get(room_id,[])):
            try: await peer.send_json({"type":"presence","event":"peer_left","participants":len(connections[room_id])})
            except Exception: pass
        if not connections.get(room_id): connections.pop(room_id,None)
