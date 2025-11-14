from typing import Iterable
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.session import get_session
from db.models.user import User
from db.models.role import Role
from db.models.permission import Permission, RolePermission
from db.models.user_role import UserRole
from core.security import decode_token


async def get_current_user(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
) -> User:
    """获取当前登录用户对象的依赖。"""
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
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")
    return user


async def get_user_permissions(user: User, session: AsyncSession) -> set[str]:
    """获取用户的权限码集合。"""
    # 汇总用户的所有角色（包含主角色与多角色）
    role_ids: list[int] = []
    if user.role_id:
        role_ids.append(user.role_id)
    extra = await session.execute(select(UserRole.role_id).where(UserRole.user_id == user.id))
    role_ids.extend([r[0] for r in extra.all()])
    role_ids = list({rid for rid in role_ids if rid})
    if not role_ids:
        return set()
    # 若任一角色为超级管理员，直接返回所有权限
    rres = await session.execute(select(Role).where(Role.id.in_(role_ids)))
    roles = rres.scalars().all()
    if any(r.is_superadmin for r in roles):
        pres = await session.execute(select(Permission.code))
        all_perms = {row[0] for row in pres.all()}
        return all_perms
    rp = await session.execute(
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.role_id.in_(role_ids))
    )
    perms = {row[0] for row in rp.all()}
    return perms


def require_permissions(*codes: str):
    async def _inner(
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> User:
        """权限校验依赖，确保用户拥有指定权限码。"""
        # 管理员 + 超级管理员拥有全部权限，普通管理员仍需按角色权限
        perms = await get_user_permissions(user, session)
        missing = [c for c in codes if c not in perms]
        if missing:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
        return user

    return _inner
