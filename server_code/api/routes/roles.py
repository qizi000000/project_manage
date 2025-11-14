from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from db.session import get_session
from db.models.role import Role
from db.models.permission import Permission, RolePermission
from db.models.user import User
from core.security import decode_token
from schemas.user import RoleOut
from schemas.permission import RolePermissionUpdate
from api.deps.auth import require_permissions

router = APIRouter(prefix="/roles", tags=["roles"])


async def require_admin(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
) -> User:
    """管理员权限依赖。"""
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
        # 仅管理员可访问角色列表（可按需调整）
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")
    return user


@router.get("/", response_model=list[RoleOut], dependencies=[Depends(require_permissions("roles.view"))])
async def list_roles(session: AsyncSession = Depends(get_session)):
    """获取所有角色列表。"""
    res = await session.execute(select(Role).order_by(Role.id))
    roles = res.scalars().all()
    return [RoleOut(id=r.id, name=r.name, is_superadmin=r.is_superadmin, remark=r.remark) for r in roles]


@router.post("/", response_model=RoleOut, dependencies=[Depends(require_permissions("roles.create"))])
async def create_role(
    name: str,
    remark: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """创建新角色。"""
    exist = await session.execute(select(Role).where(Role.name == name))
    if exist.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="角色已存在")
    role = Role(name=name, remark=remark, is_superadmin=False)
    session.add(role)
    await session.commit()
    await session.refresh(role)
    return RoleOut(id=role.id, name=role.name, is_superadmin=role.is_superadmin, remark=role.remark)


@router.delete("/{role_id}", dependencies=[Depends(require_permissions("roles.delete"))])
async def delete_role(role_id: int, session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(Role).where(Role.id == role_id))
    role = res.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    if role.is_superadmin:
        raise HTTPException(status_code=400, detail="禁止删除超级管理员角色")
    await session.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
    await session.execute(delete(Role).where(Role.id == role_id))
    await session.commit()
    return {"ok": True}


@router.get("/{role_id}/permissions", response_model=list[int], dependencies=[Depends(require_permissions("roles.view"))])
async def get_role_permissions(role_id: int, session: AsyncSession = Depends(get_session)):
    """获取角色权限列表。"""
    res = await session.execute(select(Role).where(Role.id == role_id))
    role = res.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    if role.is_superadmin:
        # 超级管理员拥有全部权限
        pres = await session.execute(select(Permission.id))
        return [row[0] for row in pres.all()]
    rp = await session.execute(select(RolePermission.permission_id).where(RolePermission.role_id == role_id))
    return [row[0] for row in rp.all()]


@router.put("/{role_id}/permissions", dependencies=[Depends(require_permissions("roles.update"))])
async def set_role_permissions(role_id: int, payload: RolePermissionUpdate, session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(Role).where(Role.id == role_id))
    role = res.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    if role.is_superadmin:
        raise HTTPException(status_code=400, detail="超级管理员不需要配置权限")
    await session.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
    # 过滤掉不存在的权限 id
    if payload.permission_ids:
        pres = await session.execute(select(Permission.id).where(Permission.id.in_(payload.permission_ids)))
        valid_ids = [row[0] for row in pres.all()]
        for pid in valid_ids:
            session.add(RolePermission(role_id=role_id, permission_id=pid))
    await session.commit()
    return {"ok": True}
