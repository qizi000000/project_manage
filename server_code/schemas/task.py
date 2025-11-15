"""任务相关的 Pydantic 模式。"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# 任务负责人信息
class TaskAssigneeInfo(BaseModel):
    id: int
    nickname: str
    username: str

# 任务输出
class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str = "待处理"
    priority: str = "中"
    assignees: List[TaskAssigneeInfo] = []
    project_id: int
    project_name: Optional[str] = None
    created_by: int
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    start_date: Optional[datetime] = None  # 任务开始日期
    estimated_days: Optional[int] = None
    due_date: Optional[datetime] = None  # 自动计算得出

# 任务创建输入
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "待处理"
    priority: str = "中"
    assignee_ids: List[int] = []  # 多个负责人ID列表
    project_id: int
    start_date: Optional[datetime] = None  # 任务开始日期
    estimated_days: Optional[int] = None

# 任务列表响应
class TaskListResponse(BaseModel):
    total: int
    items: List[TaskOut]

# 任务更新输入
class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_ids: Optional[List[int]] = None  # 多个负责人ID列表
    start_date: Optional[datetime] = None  # 任务开始日期
    estimated_days: Optional[int] = None

# 任务查询参数
class TaskQuery(BaseModel):
    page: int = 1
    page_size: int = 10
    project_id: Optional[int] = None
    assignee_id: Optional[int] = None
    status: Optional[str] = None
    priority: Optional[str] = None

# 任务评论创建输入
class TaskCommentCreate(BaseModel):
    content: str  # 评论内容
    mentioned_users: Optional[List[int]] = None  # 被@的用户ID列表