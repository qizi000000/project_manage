"""仪表盘路由：统计数据和概览信息。"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta

from db.session import get_session
from db.models.project import Project
from db.models.task import Task, TaskAssignee
from db.models.user import User
from db.models.team import Team
from api.deps.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """获取仪表盘统计数据"""

    # 项目统计
    projects_q = await session.execute(select(func.count(Project.id)))
    total_projects = projects_q.scalar()

    # 任务统计
    tasks_q = await session.execute(select(func.count(Task.id)))
    total_tasks = tasks_q.scalar()

    completed_tasks_q = await session.execute(
        select(func.count(Task.id)).where(Task.status == "已完成")
    )
    completed_tasks = completed_tasks_q.scalar()

    in_progress_tasks_q = await session.execute(
        select(func.count(Task.id)).where(Task.status == "进行中")
    )
    in_progress_tasks = in_progress_tasks_q.scalar()

    pending_tasks_q = await session.execute(
        select(func.count(Task.id)).where(Task.status == "待处理")
    )
    pending_tasks = pending_tasks_q.scalar()

    # 用户统计
    users_q = await session.execute(select(func.count(User.id)))
    total_users = users_q.scalar()

    # 团队统计
    teams_q = await session.execute(select(func.count(Team.id)))
    total_teams = teams_q.scalar()

    # 最近7天创建的任务
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_tasks_q = await session.execute(
        select(func.count(Task.id)).where(Task.created_at >= seven_days_ago)
    )
    recent_tasks = recent_tasks_q.scalar()

    # 最近7天完成的任务
    recent_completed_q = await session.execute(
        select(func.count(Task.id)).where(
            Task.status == "已完成",
            Task.updated_at >= seven_days_ago
        )
    )
    recent_completed = recent_completed_q.scalar()

    return {
        "projects": {
            "total": total_projects,
        },
        "tasks": {
            "total": total_tasks,
            "completed": completed_tasks,
            "in_progress": in_progress_tasks,
            "pending": pending_tasks,
            "recent_created": recent_tasks,
            "recent_completed": recent_completed,
        },
        "users": {
            "total": total_users,
        },
        "teams": {
            "total": total_teams,
        }
    }


@router.get("/recent-activity")
async def get_recent_activity(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    limit: int = 10
):
    """获取最近活动"""

    # 最近创建的项目
    recent_projects_q = await session.execute(
        select(Project).options(selectinload(Project.owner)).order_by(Project.created_at.desc()).limit(limit)
    )
    recent_projects = recent_projects_q.scalars().all()

    # 最近创建的任务
    recent_tasks_q = await session.execute(
        select(Task).options(selectinload(Task.creator)).order_by(Task.created_at.desc()).limit(limit)
    )
    recent_tasks = recent_tasks_q.scalars().all()

    # 最近更新的任务
    recent_updated_tasks_q = await session.execute(
        select(Task).options(selectinload(Task.creator)).where(Task.updated_at.isnot(None)).order_by(Task.updated_at.desc()).limit(limit)
    )
    recent_updated_tasks = recent_updated_tasks_q.scalars().all()

    activities = []

    # 添加项目创建活动
    for project in recent_projects:
        activities.append({
            "type": "project_created",
            "title": f"创建了项目 '{project.name}'",
            "timestamp": project.created_at.isoformat(),
            "user": project.owner.nickname or project.owner.username if project.owner else "未知用户"
        })

    # 添加任务创建活动
    for task in recent_tasks:
        activities.append({
            "type": "task_created",
            "title": f"创建了任务 '{task.title}'",
            "timestamp": task.created_at.isoformat(),
            "user": task.creator.nickname or task.creator.username if task.creator else "未知用户",
            "project": task.project.name if task.project else None
        })

    # 添加任务更新活动
    for task in recent_updated_tasks:
        if task.updated_at != task.created_at:  # 只显示真正更新的任务
            activities.append({
                "type": "task_updated",
                "title": f"更新了任务 '{task.title}'",
                "timestamp": task.updated_at.isoformat(),
                "user": task.creator.nickname or task.creator.username if task.creator else "未知用户",
                "project": task.project.name if task.project else None
            })

    # 按时间排序并限制数量
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    return activities[:limit]


@router.get("/pending-tasks")
async def get_pending_tasks(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    limit: int = 5
):
    """获取待办任务"""

    # 获取当前用户负责的任务（待处理和进行中）
    pending_tasks_q = await session.execute(
        select(Task).options(selectinload(Task.project)).join(TaskAssignee).where(
            TaskAssignee.user_id == current_user.id,
            Task.status.in_(["待处理", "进行中"])
        ).order_by(Task.created_at.desc()).limit(limit)
    )
    pending_tasks = pending_tasks_q.scalars().all()

    return [
        {
            "id": task.id,
            "title": task.title,
            "status": task.status,
            "priority": task.priority,
            "project_name": task.project.name if task.project else None,
            "created_at": task.created_at.isoformat(),
            "estimated_days": task.estimated_days
        }
        for task in pending_tasks
    ]