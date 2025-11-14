"""SQLAlchemy ORM 基类与元数据注册（中文注释）。

定义统一的 Declarative Base，并在模块加载时导入模型，
确保 Base.metadata 能收集到所有表结构用于创建/迁移。
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""

    pass


# 导入模型以注册到元数据（避免循环导入，仅在此做模块级导入）
from db.models import user  # noqa: F401
from db.models import role  # noqa: F401
from db.models import permission  # noqa: F401
from db.models import project  # noqa: F401
from db.models import team  # noqa: F401
from db.models import user_role  # noqa: F401
from db.models import notification  # noqa: F401
