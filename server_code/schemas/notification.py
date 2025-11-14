"""通知相关 Pydantic 模式。"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from enum import Enum


class NotificationType(str, Enum):
    """通知类型枚举"""
    MENTION = "mention"  # @提及
    TASK_ASSIGNED = "task_assigned"  # 任务分配
    COMMENT_REPLY = "comment_reply"  # 评论回复
    PROJECT_UPDATE = "project_update"  # 项目更新
    TEAM_INVITE = "team_invite"  # 团队邀请
    PROJECT_ASSIGNED = "project_assigned"  # 项目分配


class NotificationBase(BaseModel):
    """通知基础模式"""
    type: NotificationType
    title: str
    content: str
    related_id: Optional[int] = None
    related_type: Optional[str] = None


class NotificationCreate(NotificationBase):
    """创建通知模式"""
    user_id: int


class NotificationOut(NotificationBase):
    """通知输出模式"""
    id: int
    user_id: int
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """通知列表响应"""
    total: int
    items: list[NotificationOut]
    unread_count: int