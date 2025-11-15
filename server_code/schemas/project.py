"""项目相关 Pydantic 模式。"""

from datetime import date, datetime
from pydantic import BaseModel, Field
from typing import List
from schemas.user import UserOut


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None  # 富文本 HTML 字符串
    status: str | None = None  # planned/in_progress/completed/on_hold/cancelled
    leader_ids: List[int] | None = None  # 项目负责人ID列表（支持多个）
    team_id: int | None = None  # 所属团队ID
    development_days: int | None = None  # 开发周期（天数）
    start_date: date | None = None
    end_date: date | None = None


class ProjectUpdate(BaseModel):
    """项目更新模式，所有字段可选"""
    name: str | None = None
    description: str | None = None
    status: str | None = None
    leader_ids: List[int] | None = None  # 项目负责人ID列表（支持多个）
    team_id: int | None = None
    development_days: int | None = None
    start_date: date | None = None
    end_date: date | None = None


class ProjectBrief(BaseModel):
    id: int
    name: str
    status: str
    leader_ids: List[int] = []  # 项目负责人ID列表
    team_id: int | None = None
    development_days: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    created_at: datetime
    total_tasks: int = 0
    incomplete_tasks: int = 0

    class Config:
        from_attributes = True


class ProjectDetail(ProjectBrief):
    description: str | None = None


class AttachmentBrief(BaseModel):
    id: int
    filename: str
    url: str
    file_size: int | None = None
    uploaded_by: int | None = None
    uploaded_at: datetime
    uploader_name: str | None = None  # 上传者姓名

    class Config:
        from_attributes = True


class CommentOut(BaseModel):
    id: int
    user_id: int | None = None
    content: str
    mentioned_users: list[int] | None = None  # 被@的用户ID列表
    created_at: datetime
    # 额外的用户信息（由后端填充）
    user_nickname: str | None = None
    user_username: str | None = None
    user_role_name: str | None = None

    class Config:
        from_attributes = True

# 评论创建输入
class CommentCreate(BaseModel):
    content: str  # HTML 格式内容
    mentioned_user_ids: list[int] | None = None  # 被@的用户ID列表

# 时间线项输出
class TimelineItem(BaseModel):
    id: int
    title: str
    content: str | None = None
    occurred_at: datetime

    class Config:
        from_attributes = True

# 成员输出
class MemberOut(BaseModel):
    id: int
    username: str
    nickname: str | None = None
    email: str | None = None
    roles: List[str] = []  # 多个角色
    joined_at: datetime | None = None
    online: bool = False
    is_leader: bool = False  # 是否是项目负责人

    class Config:
        from_attributes = True


# 里程碑相关schema
class MilestoneCreate(BaseModel):
    title: str = Field(..., max_length=100)  # 限制标题长度为100字符
    description: str | None = None
    due_date: date | None = None
    status: str = "pending"


class MilestoneUpdate(BaseModel):
    title: str | None = Field(None, max_length=100)  # 限制标题长度为100字符
    description: str | None = None
    due_date: date | None = None
    status: str | None = None


class MilestoneOut(BaseModel):
    id: int
    title: str
    description: str | None = None
    due_date: date | None = None
    completed_at: datetime | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    creator: UserOut  # 创建人信息

    class Config:
        from_attributes = True
