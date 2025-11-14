"""FastAPI 应用入口。

- 负责创建应用、注册中间件与路由。
- 启动时自动创建数据库表并初始化默认管理员账号（admin/admin123）。
"""

from fastapi import FastAPI  # FastAPI应用框架
from fastapi.middleware.cors import CORSMiddleware  # CORS跨域中间件
from fastapi.staticfiles import StaticFiles  # 静态文件服务
from sqlalchemy import select,inspect  # SQLAlchemy查询和函数

from contextlib import asynccontextmanager  # 异步上下文管理器
import os  # 系统操作

from core.config import settings  # 应用配置
from core.seed_data import BASE_PERMISSIONS, BUILTIN_ROLES, DEFAULT_ADMIN  # 系统种子数据
from db.base import Base  # 数据库基类
from db.session import engine, get_session  # 数据库引擎和会话管理
from db.models.user import User  # 用户模型
from db.models.role import Role  # 角色模型
from db.models.permission import Permission  # 权限模型
from core.security import get_password_hash  # 密码加密
from api.routes.auth import router as auth_router  # 认证路由
from api.routes.projects import router as projects_router  # 项目路由
from api.routes.users import router as users_router  # 用户路由
from api.routes.roles import router as roles_router  # 角色路由
from api.routes.permissions import router as permissions_router  # 权限路由
from api.routes.ws import router as ws_router  # WebSocket路由
from api.routes.teams import router as teams_router  # 团队路由
from api.routes.tasks import router as tasks_router  # 任务路由
from api.routes.dashboard import router as dashboard_router  # 仪表盘路由
from api.routes.analytics import router as analytics_router  # 图表分析路由
from api.routes.notifications import router as notifications_router  # 通知路由


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理器。

    - 启动时：如无表则创建表，并初始化基础数据
    - 关闭时：清理资源
    """

    
    
    
    async with engine.begin() as conn:
        # 要重新创建表，请取消注释下面的代码：
        # print("删除全部数据库表...")
        # await conn.run_sync(Base.metadata.drop_all)

        print("创建全部数据库表...")
        await conn.run_sync(Base.metadata.create_all)

    # 初始化系统基础数据（只在首次创建表时执行）
    async for session in get_session():
        # 管理员角色
        super_role = await session.execute(select(Role).where(Role.name == "超级管理员"))
        super_role = super_role.scalar_one_or_none()
        if not super_role:
            print('创建内置角色与权限...')
            super_role = Role(name="超级管理员", is_superadmin=True, remark="系统内置")
            session.add(super_role)
            await session.commit()
            await session.refresh(super_role)

            # 基础权限
            for code, name, group in BASE_PERMISSIONS:
                exists = await session.execute(select(Permission).where(Permission.code == code))
                if not exists.scalar_one_or_none():
                    session.add(Permission(code=code, name=name, group=group))

            # 内置角色
            for role_name in BUILTIN_ROLES:
                exists = await session.execute(select(Role).where(Role.name == role_name))
                if not exists.scalar_one_or_none():
                    session.add(Role(name=role_name, is_superadmin=False, remark="内置"))

            # 默认管理员
            admin_exists = await session.execute(select(User).where(User.username == DEFAULT_ADMIN["username"]))
            if not admin_exists.scalar_one_or_none():
                admin_user = User(
                    username=DEFAULT_ADMIN["username"],
                    nickname=DEFAULT_ADMIN["nickname"],
                    password_hash=get_password_hash(DEFAULT_ADMIN["password"]),
                    is_admin=DEFAULT_ADMIN["is_admin"],
                    role_id=super_role.id,
                )
                session.add(admin_user)
                admin_user = User(
                    username='erdan',
                    nickname='二蛋',
                    password_hash=get_password_hash('123456'),
                    is_admin=False,
                    role_id=3,
                )
                session.add(admin_user)

                admin_user = User(
                    username='sandan',
                    nickname='三蛋',
                    password_hash=get_password_hash('123456'),
                    is_admin=False,
                    role_id=4,
                )
                session.add(admin_user)


            await session.commit()
        break
    print("应用启动完成")
    yield
    print("应用关闭")


# 创建FastAPI应用实例
app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# 创建uploads目录（如果不存在）用于存储上传的文件
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "projects"), exist_ok=True)

# 挂载静态文件目录
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(ws_router)  # WebSocket实时通信接口（无前缀）
app.include_router(auth_router, prefix=settings.API_PREFIX)  # 用户认证相关接口
app.include_router(users_router, prefix=settings.API_PREFIX)  # 用户管理相关接口
app.include_router(roles_router, prefix=settings.API_PREFIX)  # 角色管理相关接口
app.include_router(teams_router, prefix=settings.API_PREFIX)  # 团队管理相关接口
app.include_router(tasks_router, prefix=settings.API_PREFIX)  # 任务管理相关接口
app.include_router(projects_router, prefix=settings.API_PREFIX)  # 项目管理相关接口
app.include_router(dashboard_router, prefix=settings.API_PREFIX)  # 仪表盘相关接口
app.include_router(analytics_router, prefix=settings.API_PREFIX)  # 图表分析相关接口
app.include_router(permissions_router, prefix=settings.API_PREFIX)  # 权限管理相关接口
app.include_router(notifications_router, prefix=settings.API_PREFIX)  # 通知相关接口


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
