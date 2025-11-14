"""角色模型。

提供基础角色支持：
- id, name 唯一
- is_superadmin 标记是否为超级管理员（拥有全部权限）
- remark, created_at 记录信息
"""

from datetime import datetime
from sqlalchemy import Integer, String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base

# 角色模型
class Role(Base):
    """角色模型"""
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    is_superadmin: Mapped[bool] = mapped_column(Boolean, default=False)
    remark: Mapped[str | None] = mapped_column(String(255), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
