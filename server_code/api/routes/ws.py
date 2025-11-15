from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from core.security import decode_token
from db.session import get_session
from db.models.user import User

router = APIRouter()

class ConnectionManager:
    # 管理 WebSocket 连接
    def __init__(self):
        self.active: dict[int, WebSocket] = {}
    # 连接用户
    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active[user_id] = websocket
    # 断开用户
    def disconnect(self, user_id: int):
        self.active.pop(user_id, None)
    # 获取用户连接
    def get(self, user_id: int) -> WebSocket | None:
        return self.active.get(user_id)
    # 广播消息给所有连接的用户
    async def broadcast(self, message: dict):
        for connection in self.active.values():
            try:
                await connection.send_json(message)
            except Exception:
                # 忽略发送失败的连接
                pass

manager = ConnectionManager()

async def authenticate(websocket: WebSocket) -> int | None:
    token = websocket.query_params.get("token")
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    try:
        return int(payload.get("sub"))
    except Exception:
        return None

@router.websocket("/ws")
async def ws_endpoint(websocket: WebSocket, session: AsyncSession = Depends(get_session)):
    user_id = await authenticate(websocket)
    if not user_id:
        await websocket.close(code=4401)
        return
    # 校验用户存在与激活
    res = await session.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user or not user.is_active:
        await websocket.close(code=4403)
        return

    # 标记在线 + 更新时间
    user.online = True
    user.last_login = datetime.utcnow()
    await session.commit()

    await manager.connect(user_id, websocket)
    
    # 广播用户上线消息
    await manager.broadcast({
        "type": "user_status_change",
        "user_id": user_id,
        "online": True
    })

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            if msg_type == "ping":
                await websocket.send_json({"type": "pong", "ts": datetime.utcnow().isoformat()})
            else:
                # 预留：后续聊天等消息类型
                await websocket.send_json({"type": "ack"})
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(user_id)
        # 清理在线状态
        res = await session.execute(select(User).where(User.id == user_id))
        user = res.scalar_one_or_none()
        if user:
            user.online = False
            await session.commit()
        
        # 广播用户下线消息
        await manager.broadcast({
            "type": "user_status_change",
            "user_id": user_id,
            "online": False
        })
