from typing import List, Optional
from pydantic import BaseModel


class PermissionOut(BaseModel):
    id: int
    code: str
    name: str
    group: str
    description: Optional[str] = None


class PermissionGroupOut(BaseModel):
    group: str
    items: List[PermissionOut]


class RolePermissionUpdate(BaseModel):
    permission_ids: List[int]
