"""数据库会话与引擎（中文注释）。

使用 SQLAlchemy 2.x 异步引擎 + 会话工厂：
- create_async_engine 创建异步引擎
- sessionmaker 生成 AsyncSession 工厂
- 依赖注入 get_session() 用于 FastAPI 路由
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings

# 创建异步引擎；生产环境可按需开启 echo 以调试 SQL
engine = create_async_engine(settings.DATABASE_URL, future=True, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncSession:
    """提供一次性的异步会话，用于 FastAPI 依赖注入。"""
    async with AsyncSessionLocal() as session:
        yield session
