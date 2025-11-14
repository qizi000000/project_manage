"""认证相关路由（中文注释）。

当前仅包含登录接口：
- POST /auth/login：校验凭证并返回 JWT 访问令牌
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.session import get_session
from db.models.user import User, LoginLog
from db.models.role import Role
from core.security import verify_password, create_access_token, decode_token, get_password_hash
from schemas.auth import LoginRequest, Token, Me
from schemas.user import UserProfileUpdate, UserPasswordChange, LoginLogOut
from api.deps.auth import get_current_user, get_user_permissions

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(
    payload: LoginRequest, 
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """用户名密码登录，返回 access_token。"""
    # 根据用户名查询用户
    q = await session.execute(select(User).where(User.username == payload.username))
    user = q.scalar_one_or_none()
    # 校验密码
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")

    # 记录登录日志
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    
    login_log = LoginLog(
        user_id=user.id,
        ip_address=client_ip,
        user_agent=user_agent
    )
    session.add(login_log)
    
    # 更新最后登录时间
    user.last_login = login_log.created_at
    session.add(user)
    
    await session.commit()

    # 生成访问令牌
    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)


@router.get("/me", response_model=Me)
async def me(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
):
    """获取当前登录用户的简要信息。

    从 Authorization: Bearer <token> 解析并校验 JWT，返回用户 id 与用户名。
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未提供凭证")
    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="凭证无效或已过期")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="凭证无效")

    q = await session.execute(select(User).where(User.id == int(user_id)))
    user = q.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")
    
    # 获取角色信息
    role_name = None
    if user.role_id:
        role_q = await session.execute(select(Role).where(Role.id == user.role_id))
        role = role_q.scalar_one_or_none()
        if role:
            role_name = role.name
    
    return Me(
        id=user.id, 
        username=user.username,
        nickname=user.nickname,
        email=user.email,
        phone=user.phone,
        wechat=user.wechat,
        avatar=user.avatar,
        role_name=role_name,
        is_admin=user.is_admin,
        remark=user.remark,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.get("/permissions", response_model=list[str])
async def my_permissions(current: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    perms = await get_user_permissions(current, session)
    return sorted(perms)


@router.put("/me", response_model=Me)
async def update_me(
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """更新当前用户的个人资料"""
    # 更新用户信息
    if payload.nickname is not None:
        current_user.nickname = payload.nickname
    if payload.email is not None:
        current_user.email = payload.email
    if payload.phone is not None:
        current_user.phone = payload.phone
    if payload.wechat is not None:
        current_user.wechat = payload.wechat
    if payload.avatar is not None:
        current_user.avatar = payload.avatar
    if payload.remark is not None:
        current_user.remark = payload.remark
    
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    
    # 获取角色信息
    role_name = None
    if current_user.role_id:
        role_q = await session.execute(select(Role).where(Role.id == current_user.role_id))
        role = role_q.scalar_one_or_none()
        if role:
            role_name = role.name
    
    return Me(
        id=current_user.id, 
        username=current_user.username,
        nickname=current_user.nickname,
        email=current_user.email,
        phone=current_user.phone,
        wechat=current_user.wechat,
        avatar=current_user.avatar,
        role_name=role_name,
        is_admin=current_user.is_admin,
        remark=current_user.remark,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.put("/password")
async def change_password(
    payload: UserPasswordChange,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """修改当前用户的密码"""
    # 验证当前密码
    if not verify_password(payload.old_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前密码错误")
    
    # 更新密码
    current_user.password_hash = get_password_hash(payload.new_password)
    session.add(current_user)
    await session.commit()
    
    return {"message": "密码修改成功"}


@router.get("/login-logs", response_model=list[LoginLogOut])
async def get_login_logs(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    limit: int = 20
):
    """获取当前用户的登录日志"""
    from db.models.user import LoginLog
    
    result = await session.execute(
        select(LoginLog)
        .where(LoginLog.user_id == current_user.id)
        .order_by(LoginLog.created_at.desc())
        .limit(limit)
    )
    
    logs = result.scalars().all()
    return logs


@router.get("/permissions")
async def get_user_permissions_route(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """获取当前用户的权限列表"""
    from api.deps.auth import get_user_permissions
    permissions = await get_user_permissions(current_user, session)
    return list(permissions)
