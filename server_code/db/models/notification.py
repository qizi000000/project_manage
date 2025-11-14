"""通知模型（中文注释）。

定义用户通知相关的数据库模型。
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from db.base import Base


class NotificationType(str, enum.Enum):
    """通知类型枚举"""
    MENTION = "mention"  # @提及
    TASK_ASSIGNED = "task_assigned"  # 任务分配
    COMMENT_REPLY = "comment_reply"  # 评论回复
    PROJECT_UPDATE = "project_update"  # 项目更新
    TEAM_INVITE = "team_invite"  # 团队邀请
    PROJECT_ASSIGNED = "project_assigned"  # 项目分配


class Notification(Base):
    """通知模型"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(Enum(NotificationType), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    related_id = Column(Integer, nullable=True)  # 相关对象的ID（如项目ID、任务ID等）
    related_type = Column(String(50), nullable=True)  # 相关对象类型（如project, task等）
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关联
    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.type}, is_read={self.is_read})>"