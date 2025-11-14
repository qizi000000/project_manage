"""用户与角色相关的 Pydantic 模式。"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# 角色输出
class RoleOut(BaseModel):
    id: int
    name: str
    is_superadmin: bool = False
    remark: Optional[str] = None

# 用户输出
class UserOut(BaseModel):
    id: int
    username: str
    nickname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    wechat: Optional[str] = None
    avatar: Optional[str] = None
    is_admin: bool = False
    is_active: bool = True
    role_id: Optional[int] = None
    roles: List[str] = Field(default_factory=list)
    remark: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    online: bool = False

# 用户创建输入
class UserCreate(BaseModel):
    username: str
    password: str
    nickname: Optional[str] = None
    is_admin: bool = False
    role_id: Optional[int] = None
    role_ids: Optional[List[int]] = None
    remark: Optional[str] = None

# 用户列表响应
class UserListResponse(BaseModel):
    total: int
    items: List[UserOut]

# 用户查询参数
class UserQuery(BaseModel):
    page: int = 1
    page_size: int = 10
    username: Optional[str] = None
    nickname: Optional[str] = None
    remark: Optional[str] = None
    role_id: Optional[int] = None
    created_from: Optional[datetime] = Field(default=None, description="起始创建时间")
    created_to: Optional[datetime] = Field(default=None, description="结束创建时间")


class UserActiveUpdate(BaseModel):
    is_active: bool


class UserPasswordReset(BaseModel):
    password: str


class UserPasswordUpdate(BaseModel):
    """用户编辑时修改密码"""
    new_password: str = Field(..., min_length=6, description="新密码，至少6位")


class UserUpdate(BaseModel):
    username: Optional[str] = None
    nickname: Optional[str] = None
    is_admin: Optional[bool] = None
    role_id: Optional[int] = None
    role_ids: Optional[List[int]] = None
    remark: Optional[str] = None


class UserProfileUpdate(BaseModel):
    """用户个人资料更新（仅允许用户自己修改的字段）"""
    nickname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    wechat: Optional[str] = None
    avatar: Optional[str] = None
    remark: Optional[str] = None


class UserPasswordChange(BaseModel):
    """用户修改自己的密码"""
    old_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=6, description="新密码，至少6位")


class LoginLogOut(BaseModel):
    """登录日志输出"""
    id: int
    ip_address: str
    user_agent: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
