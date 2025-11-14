"""团队相关 Pydantic 模式。"""

from datetime import datetime
from pydantic import BaseModel
from typing import List


class TeamCreate(BaseModel):
    name: str
    description: str | None = None
    member_ids: List[int] | None = None  # 团队成员ID列表


class TeamUpdate(BaseModel):
    """团队更新模式，所有字段可选"""
    name: str | None = None
    description: str | None = None


class TeamBrief(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime
    member_count: int = 0

    class Config:
        from_attributes = True


class TeamDetail(TeamBrief):
    members: List[dict] = []  # 成员列表，包含用户信息