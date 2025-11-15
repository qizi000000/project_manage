"""项目相关模型（Project、成员、附件、评论、时间线）。

注意：此为最小可用模型，后续可根据业务扩展字段与索引。
"""

from __future__ import annotations

from datetime import datetime, date
from enum import StrEnum

from sqlalchemy import (
    Integer,
    String,
    Text,
    Date,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from db.models.user import User
# 项目状态枚举
class ProjectStatus(StrEnum):
    planned = "planned"
    in_progress = "in_progress"
    completed = "completed"
    on_hold = "on_hold"
    cancelled = "cancelled"

#  项目模型
class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    status: Mapped[str] = mapped_column(String(32), default=ProjectStatus.planned)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), default=None)  # 项目负责人
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), default=None)  # 所属团队
    development_days: Mapped[int | None] = mapped_column(Integer, default=None)  # 开发周期（天数）
    start_date: Mapped[date | None] = mapped_column(Date, default=None)
    end_date: Mapped[date | None] = mapped_column(Date, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 关系（懒加载，按需使用）
    owner: Mapped[User | None] = relationship("User", foreign_keys=[owner_id])
    members: Mapped[list[ProjectMember]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    attachments: Mapped[list[ProjectAttachment]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    comments: Mapped[list[ProjectComment]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    timeline: Mapped[list[ProjectTimeline]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    milestones: Mapped[list[ProjectMilestone]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )

# 项目成员关联模型
class ProjectMember(Base):
    __tablename__ = "project_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str | None] = mapped_column(String(50), default=None)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped[Project] = relationship(back_populates="members")


class ProjectAttachment(Base):
    __tablename__ = "project_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(500))
    file_size: Mapped[int | None] = mapped_column(Integer, default=None)  # 文件大小（字节）
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), default=None)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped[Project] = relationship(back_populates="attachments")


class ProjectComment(Base):
    __tablename__ = "project_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), default=None)
    content: Mapped[str] = mapped_column(Text)  # HTML 格式内容
    mentioned_users: Mapped[str | None] = mapped_column(Text, default=None)  # JSON 数组存储被@的用户ID列表
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped[Project] = relationship(back_populates="comments")


class ProjectTimeline(Base):
    __tablename__ = "project_timeline"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str | None] = mapped_column(Text, default=None)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped[Project] = relationship(back_populates="timeline")


class ProjectMilestone(Base):
    """项目里程碑模型"""
    __tablename__ = "project_milestones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)  # 创建人
    title: Mapped[str] = mapped_column(String(100))  # 限制标题长度为100字符
    description: Mapped[str | None] = mapped_column(Text, default=None)
    due_date: Mapped[date | None] = mapped_column(Date, default=None)  # 计划完成日期
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)  # 实际完成时间
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending, completed, overdue
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    project: Mapped[Project] = relationship(back_populates="milestones")
    creator: Mapped[User] = relationship("User", foreign_keys=[created_by])
