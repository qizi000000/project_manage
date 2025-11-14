from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.session import get_session
from db.models.user import User
from db.models.permission import Permission
from core.security import decode_token
from schemas.permission import PermissionOut, PermissionGroupOut
from api.deps.auth import require_permissions

router = APIRouter(prefix="/permissions", tags=["permissions"])


async def require_admin(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未提供凭证")
    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="凭证无效或已过期")
    user_id = int(payload.get("sub", 0))
    q = await session.execute(select(User).where(User.id == user_id))
    user = q.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")
    return user


@router.get("/", response_model=list[PermissionOut], dependencies=[Depends(require_permissions("roles.view"))])
async def list_permissions(session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(Permission).order_by(Permission.group, Permission.id))
    items = res.scalars().all()
    return [PermissionOut(id=p.id, code=p.code, name=p.name, group=p.group, description=p.description) for p in items]


@router.get("/grouped", response_model=list[PermissionGroupOut], dependencies=[Depends(require_permissions("roles.view"))])
async def list_permissions_grouped(session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(Permission).order_by(Permission.group, Permission.id))
    items = res.scalars().all()
    groups: dict[str, list[PermissionOut]] = {}
    for p in items:
        groups.setdefault(p.group, []).append(PermissionOut(id=p.id, code=p.code, name=p.name, group=p.group, description=p.description))
    return [{"group": g, "items": v} for g, v in groups.items()]
