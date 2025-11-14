"""权限模型：基础权限与角色权限关联（RBAC）。"""

from sqlalchemy import Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 权限唯一编码，如：users.read、users.create、roles.assign、projects.manage
    code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    # 显示名称
    name: Mapped[str] = mapped_column(String(100))
    # 分组（模块）名，如 users/roles/projects
    group: Mapped[str] = mapped_column(String(50))
    # 描述
    description: Mapped[str | None] = mapped_column(String(255), default=None)

# 角色权限关联模型
class RolePermission(Base):
    __tablename__ = "role_permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 角色 ID
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"))
    # 权限 ID
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id", ondelete="CASCADE"))
    # 角色与权限关系
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )
