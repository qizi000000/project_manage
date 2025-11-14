from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, delete
from datetime import datetime, timedelta

from db.session import get_session
from db.models.user import User
from db.models.role import Role
from db.models.user_role import UserRole
from core.security import decode_token, get_password_hash
from schemas.user import UserOut, UserCreate, UserListResponse, UserActiveUpdate, UserPasswordReset, UserPasswordUpdate, UserUpdate
from api.deps.auth import require_permissions

router = APIRouter(prefix="/users", tags=["users"])

# 管理员权限依赖
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
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")
    return user

# 用户模型转换函数
def to_user_out(u: User) -> UserOut:
    return UserOut(
        id=u.id,
        username=u.username,
        nickname=u.nickname,
        is_admin=u.is_admin,
        is_active=u.is_active,
        role_id=u.role_id,
    roles=[],
        remark=u.remark,
    created_at=u.created_at,
    last_login=u.last_login,
    online=u.online,
    )


@router.get("/", response_model=UserListResponse, dependencies=[Depends(require_permissions("users.view"))])
async def list_users(
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    q: str | None = None,
    role_id: int | None = None,
    online: bool | None = None,
):
    """分页查询用户列表，支持多条件过滤。"""
    filters = []
    if q:
        like = f"%{q}%"
        filters.append(or_(User.username.like(like), User.nickname.like(like), User.remark.like(like)))
    if role_id:
        # 同时匹配主角色或附加多角色
        subq = select(UserRole.user_id).where(UserRole.role_id == role_id)
        filters.append(or_(User.role_id == role_id, User.id.in_(subq)))

    if online is not None:
        # 依据数据库 online 字段过滤
        filters.append(User.online == online)

    base_stmt = select(User).where(and_(*filters)) if filters else select(User)
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await session.execute(count_stmt)).scalar_one()

    stmt = base_stmt.order_by(User.id.desc()).offset((page - 1) * page_size).limit(page_size)
    res = await session.execute(stmt)
    users = res.scalars().all()
    items = []
    for u in users:
        out = to_user_out(u)
        # 查询主角色
        role_names = []
        if u.role_id:
            main_role = await session.execute(select(Role.name).where(Role.id == u.role_id))
            main_role_name = main_role.scalar_one_or_none()
            if main_role_name:
                role_names.append(main_role_name)
        # 查询附加角色
        extra = await session.execute(select(UserRole.role_id).where(UserRole.user_id == u.id))
        extra_role_ids = [r[0] for r in extra.all()]
        if extra_role_ids:
            extra_roles = await session.execute(select(Role.name).where(Role.id.in_(extra_role_ids)))
            role_names.extend([r[0] for r in extra_roles.all() if r[0] and r[0] not in role_names])
        out.roles = role_names
        items.append(out)
    return {"total": total, "items": items}


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int, session: AsyncSession = Depends(get_session)):
    """获取单个用户信息。"""
    res = await session.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    out = to_user_out(user)
    extra = await session.execute(select(UserRole.role_id).where(UserRole.user_id == user.id))
    out.roles = [r[0] for r in extra.all()]
    return out


@router.post("/", response_model=UserOut, dependencies=[Depends(require_permissions("users.create"))])
async def create_user(
    payload: UserCreate,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    """创建新用户。"""
    exist = await session.execute(select(User).where(User.username == payload.username))
    if exist.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if payload.role_id:
        r = await session.execute(select(Role).where(Role.id == payload.role_id))
        if not r.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="角色不存在")
    user = User(
        username=payload.username,
        nickname=payload.nickname,
        password_hash=get_password_hash(payload.password),
        is_admin=payload.is_admin,
        role_id=payload.role_id,
        remark=payload.remark,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    # 绑定多角色（附加）
    if getattr(payload, "role_ids", None):
        for rid in payload.role_ids or []:
            if not rid:
                continue
            r = await session.execute(select(Role).where(Role.id == rid))
            if not r.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="角色不存在")
            session.add(UserRole(user_id=user.id, role_id=rid))
        await session.commit()
    out = to_user_out(user)
    extra = await session.execute(select(UserRole.role_id).where(UserRole.user_id == user.id))
    out.roles = [r[0] for r in extra.all()]
    return out


@router.patch("/{user_id}/active", dependencies=[Depends(require_permissions("users.update"))])
async def set_user_active(user_id: int, payload: UserActiveUpdate, _: User = Depends(require_admin), session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.is_active = payload.is_active
    await session.commit()
    return {"ok": True}


@router.post("/{user_id}/reset_password", dependencies=[Depends(require_permissions("users.update"))])
async def reset_password(user_id: int, payload: UserPasswordReset, _: User = Depends(require_admin), session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.password_hash = get_password_hash(payload.password)
    await session.commit()
    return {"ok": True}


@router.put("/{user_id}/password", dependencies=[Depends(require_permissions("users.update"))])
async def update_password(user_id: int, payload: UserPasswordUpdate, _: User = Depends(require_admin), session: AsyncSession = Depends(get_session)):
    """编辑用户时修改密码"""
    res = await session.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.password_hash = get_password_hash(payload.new_password)
    await session.commit()
    return {"ok": True}


@router.patch("/{user_id}", response_model=UserOut, dependencies=[Depends(require_permissions("users.update"))])
async def update_user(user_id: int, payload: UserUpdate, _: User = Depends(require_admin), session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    # 检查用户名变更唯一性
    if payload.username and payload.username != user.username:
        exist = await session.execute(select(User).where(User.username == payload.username))
        if exist.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="用户名已存在")
        user.username = payload.username
    if payload.nickname is not None:
        user.nickname = payload.nickname
    if payload.is_admin is not None:
        user.is_admin = payload.is_admin
    if payload.role_id is not None:
        # 校验角色存在
        if payload.role_id:
            r = await session.execute(select(Role).where(Role.id == payload.role_id))
            if not r.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="角色不存在")
        user.role_id = payload.role_id
    # 覆盖多角色列表
    if getattr(payload, "role_ids", None) is not None:
        await session.execute(delete(UserRole).where(UserRole.user_id == user.id))
        for rid in payload.role_ids or []:
            if not rid:
                continue
            r = await session.execute(select(Role).where(Role.id == rid))
            if not r.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="角色不存在")
            session.add(UserRole(user_id=user.id, role_id=rid))
    if payload.remark is not None:
        user.remark = payload.remark
    await session.commit()
    await session.refresh(user)
    out = to_user_out(user)
    extra = await session.execute(select(UserRole.role_id).where(UserRole.user_id == user.id))
    out.roles = [r[0] for r in extra.all()]
    return out
