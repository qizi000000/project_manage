"""认证相关的 Pydantic 模式定义（中文注释）。

- LoginRequest：登录请求体（用户名/密码）
- Token：登录成功返回的访问令牌结构
"""

from pydantic import BaseModel
from datetime import datetime


class LoginRequest(BaseModel):
    """登录请求体。"""

    username: str  # 用户名
    password: str  # 密码


class Token(BaseModel):
    """访问令牌响应。"""

    access_token: str  # JWT 字符串
    token_type: str = "bearer"  # 令牌类型，固定为 bearer


class Me(BaseModel):
    """当前用户信息（精简版）。"""

    id: int
    username: str
    nickname: str | None = None
    email: str | None = None
    phone: str | None = None
    wechat: str | None = None
    avatar: str | None = None
    role_name: str | None = None  # 角色名称
    is_admin: bool = False  # 是否管理员
    remark: str | None = None
    created_at: datetime | None = None
    last_login: datetime | None = None
