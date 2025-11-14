"""用户模型（中文注释）。

字段：
- id: 主键，自增
- username: 用户名，唯一索引
- password_hash: 密码哈希
- is_active: 是否活跃
"""
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base


class User(Base):
    __tablename__ = "users"

    # 主键 ID
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # 用户名（唯一）
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    # 昵称
    nickname: Mapped[str | None] = mapped_column(String(50), default=None)
    # 邮箱
    email: Mapped[str | None] = mapped_column(String(100), default=None)
    # 电话
    phone: Mapped[str | None] = mapped_column(String(20), default=None)
    # 微信
    wechat: Mapped[str | None] = mapped_column(String(50), default=None)
    # 头像
    avatar: Mapped[str | None] = mapped_column(String(255), default=None)
    # 密码哈希
    password_hash: Mapped[str] = mapped_column(String(255))
    # 是否管理员
    is_admin: Mapped[bool] = mapped_column(default=False)
    # 备注
    remark: Mapped[str | None] = mapped_column(String(255), default=None)
    # 角色 ID（可为空）
    role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id"), default=None)
    # 是否激活
    is_active: Mapped[bool] = mapped_column(default=True)
    # 注册时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    # 最后登录时间
    last_login: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    # 是否在线
    online: Mapped[bool] = mapped_column(default=False)

    # 关联关系
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class LoginLog(Base):
    """登录日志模型"""
    __tablename__ = "login_logs"

    # 主键 ID
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # 用户 ID
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    # IP 地址
    ip_address: Mapped[str] = mapped_column(String(45))  # IPv6 最大 45 字符
    # User Agent
    user_agent: Mapped[str | None] = mapped_column(String(500), default=None)
    # 登录时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
