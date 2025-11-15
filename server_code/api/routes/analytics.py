"""图表分析路由：提供各种统计图表数据。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from typing import List

from db.session import get_session
from db.models.project import Project
from db.models.task import Task
from db.models.user import User
from db.models.team import Team
from db.models.role import Role
from api.deps.auth import get_current_user, require_permissions

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/projects", dependencies=[Depends(require_permissions("analytics.view"))])
async def get_projects_analytics(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """获取项目分析数据"""

    # 项目状态分布
    status_query = await session.execute(
        select(Project.status, func.count(Project.id)).group_by(Project.status)
    )
    status_data = [{"status": row[0], "count": row[1]} for row in status_query.all()]

    # 项目创建时间趋势（按月统计）
    current_year = datetime.now().year
    monthly_query = await session.execute(
        select(
            extract('month', Project.created_at).label('month'),
            func.count(Project.id)
        ).where(
            extract('year', Project.created_at) == current_year
        ).group_by(extract('month', Project.created_at)).order_by(extract('month', Project.created_at))
    )
    monthly_data = [{"month": int(row[0]), "count": row[1]} for row in monthly_query.all()]

    # 项目负责人分布
    owner_query = await session.execute(
        select(
            User.username,
            func.count(Project.id)
        ).join(Project.owner).group_by(User.id, User.username).order_by(func.count(Project.id).desc())
    )
    owner_data = [{"owner": row[0], "count": row[1]} for row in owner_query.all()]

    # 项目团队分布
    team_query = await session.execute(
        select(
            Team.name,
            func.count(Project.id)
        ).join(Project.team).group_by(Team.id, Team.name).order_by(func.count(Project.id).desc())
    )
    team_data = [{"team": row[0], "count": row[1]} for row in team_query.all()]

    # 项目完成率统计
    total_projects_query = await session.execute(select(func.count(Project.id)))
    total_projects = total_projects_query.scalar()

    completed_projects_query = await session.execute(
        select(func.count(Project.id)).where(Project.status == "已完成")
    )
    completed_projects = completed_projects_query.scalar()

    completion_rate = round((completed_projects / total_projects * 100), 2) if total_projects > 0 else 0

    # 逾期项目统计
    overdue_projects_query = await session.execute(
        select(func.count(Project.id)).where(
            Project.end_date < datetime.now().date(),
            Project.status != "已完成"
        )
    )
    overdue_projects = overdue_projects_query.scalar()

    # 最近30天活跃项目（有任务更新的项目）
    thirty_days_ago = datetime.now() - timedelta(days=30)
    active_projects_query = await session.execute(
        select(func.count(func.distinct(Task.project_id))).join(Task.project).where(
            Task.updated_at >= thirty_days_ago
        )
    )
    active_projects = active_projects_query.scalar() or 0

    # 项目平均工期（已完成项目的平均天数）
    avg_duration_query = await session.execute(
        select(
            func.avg(
                func.datediff(Project.end_date, Project.start_date)
            )
        ).where(
            Project.status == "已完成",
            Project.start_date.isnot(None),
            Project.end_date.isnot(None)
        )
    )
    avg_duration = round(avg_duration_query.scalar() or 0, 1)

    return {
        "status_distribution": status_data,
        "monthly_trend": monthly_data,
        "owner_distribution": owner_data,
        "team_distribution": team_data,
        "summary": {
            "total_projects": total_projects,
            "completed_projects": completed_projects,
            "completion_rate": completion_rate,
            "overdue_projects": overdue_projects,
            "active_projects": active_projects,
            "avg_duration_days": avg_duration
        }
    }


@router.get("/tasks", dependencies=[Depends(require_permissions("analytics.view"))])
async def get_tasks_analytics(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """获取任务分析数据"""

    # 任务状态分布
    status_query = await session.execute(
        select(Task.status, func.count(Task.id)).group_by(Task.status)
    )
    status_data = [{"status": row[0], "count": row[1]} for row in status_query.all()]

    # 任务优先级分布
    priority_query = await session.execute(
        select(Task.priority, func.count(Task.id)).where(Task.priority.isnot(None)).group_by(Task.priority)
    )
    priority_data = [{"priority": row[0], "count": row[1]} for row in priority_query.all()]

    # 任务完成时间趋势（按周统计最近12周）
    twelve_weeks_ago = datetime.now() - timedelta(weeks=12)
    weekly_completion_query = await session.execute(
        select(
            func.date_format(Task.updated_at, '%Y-%m-%d').label('week'),
            func.count(Task.id)
        ).where(
            Task.status == "已完成",
            Task.updated_at >= twelve_weeks_ago
        ).group_by(func.date_format(Task.updated_at, '%Y-%m-%d')).order_by(func.date_format(Task.updated_at, '%Y-%m-%d'))
    )
    weekly_data = [{"week": row[0], "count": row[1]} for row in weekly_completion_query.all()]

    # 任务统计汇总
    total_tasks_query = await session.execute(select(func.count(Task.id)))
    total_tasks = total_tasks_query.scalar()

    completed_tasks_query = await session.execute(
        select(func.count(Task.id)).where(Task.status == "已完成")
    )
    completed_tasks = completed_tasks_query.scalar()

    completion_rate = round((completed_tasks / total_tasks * 100), 2) if total_tasks > 0 else 0

    # 逾期任务统计
    overdue_tasks_query = await session.execute(
        select(func.count(Task.id)).where(
            Task.due_date < datetime.now().date(),
            Task.status != "已完成"
        )
    )
    overdue_tasks = overdue_tasks_query.scalar()

    return {
        "status_distribution": status_data,
        "priority_distribution": priority_data,
        "weekly_completion_trend": weekly_data,
        "summary": {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "overdue_tasks": overdue_tasks,
            "completion_rate": completion_rate
        }
    }


@router.get("/users", dependencies=[Depends(require_permissions("analytics.view"))])
async def get_users_analytics(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """获取用户分析数据"""

    # 用户角色分布
    role_query = await session.execute(
        select(Role.name, func.count(User.id)).join(User, Role.id == User.role_id).group_by(Role.id, Role.name)
    )
    role_data = [{"role": row[0], "count": row[1]} for row in role_query.all()]

    # 用户注册时间趋势（按月统计）
    current_year = datetime.now().year
    monthly_query = await session.execute(
        select(
            extract('month', User.created_at).label('month'),
            func.count(User.id)
        ).where(
            extract('year', User.created_at) == current_year
        ).group_by(extract('month', User.created_at)).order_by(extract('month', User.created_at))
    )
    monthly_data = [{"month": int(row[0]), "count": row[1]} for row in monthly_query.all()]

    # 用户活跃度（最近30天登录的用户）
    thirty_days_ago = datetime.now() - timedelta(days=30)
    active_users_query = await session.execute(
        select(func.count(User.id)).where(User.last_login >= thirty_days_ago)
    )
    active_users = active_users_query.scalar()

    total_users_query = await session.execute(select(func.count(User.id)))
    total_users = total_users_query.scalar()

    return {
        "role_distribution": role_data,
        "monthly_registration_trend": monthly_data,
        "active_users": active_users,
        "total_users": total_users,
        "activity_rate": round((active_users / total_users * 100), 2) if total_users > 0 else 0
    }


@router.get("/teams", dependencies=[Depends(require_permissions("analytics.view"))])
async def get_teams_analytics(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """获取团队分析数据"""

    # 团队成员数量分布
    from db.models.team import TeamMember
    team_members_query = await session.execute(
        select(
            Team.name,
            func.count(TeamMember.id)
        ).join(TeamMember, Team.id == TeamMember.team_id).group_by(Team.id, Team.name).order_by(func.count(TeamMember.id).desc())
    )
    team_members_data = [{"team": row[0], "member_count": row[1]} for row in team_members_query.all()]

    # 团队项目数量分布
    team_projects_query = await session.execute(
        select(
            Team.name,
            func.count(Project.id)
        ).join(Project, Team.id == Project.team_id).group_by(Team.id, Team.name).order_by(func.count(Project.id).desc())
    )
    team_projects_data = [{"team": row[0], "project_count": row[1]} for row in team_projects_query.all()]

    return {
        "team_members_distribution": team_members_data,
        "team_projects_distribution": team_projects_data
    }


@router.get("/roles", dependencies=[Depends(require_permissions("analytics.view"))])
async def get_roles_analytics(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """获取角色分析数据"""

    # 角色权限数量分布
    from db.models.permission import RolePermission
    role_permissions_query = await session.execute(
        select(
            Role.name,
            func.count(RolePermission.id).label('permission_count')
        ).join(RolePermission, Role.id == RolePermission.role_id).group_by(Role.id, Role.name).order_by(func.count(RolePermission.id).desc())
    )
    role_permissions_data = [{"role": row[0], "permission_count": row[1]} for row in role_permissions_query.all()]

    # 角色用户数量分布
    role_users_query = await session.execute(
        select(
            Role.name,
            func.count(User.id)
        ).join(User, Role.id == User.role_id).group_by(Role.id, Role.name).order_by(func.count(User.id).desc())
    )
    role_users_data = [{"role": row[0], "user_count": row[1]} for row in role_users_query.all()]

    return {
        "role_permissions_distribution": role_permissions_data,
        "role_users_distribution": role_users_data
    }


@router.delete("/data/{data_type}", dependencies=[Depends(require_permissions("analytics.delete"))])
async def delete_analytics_data(
    data_type: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """删除分析数据（管理员功能）"""

    # 这里可以实现删除特定类型分析数据的逻辑
    # 例如清理旧的统计数据、日志等

    supported_types = ["old_logs", "temp_data", "cache"]

    if data_type not in supported_types:
        raise HTTPException(status_code=400, detail=f"不支持的数据类型: {data_type}")

    # 实际的删除逻辑根据需求实现
    # 这里只是示例

    return {"message": f"已清理 {data_type} 数据"}


@router.get("/export/{report_type}", dependencies=[Depends(require_permissions("analytics.export"))])
async def export_analytics_report(
    report_type: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """导出分析报告"""

    supported_types = ["projects", "tasks", "users", "teams", "roles"]

    if report_type not in supported_types:
        raise HTTPException(status_code=400, detail=f"不支持的报告类型: {report_type}")

    # 根据报告类型获取数据
    if report_type == "projects":
        data = await get_projects_analytics(session, current_user)
    elif report_type == "tasks":
        data = await get_tasks_analytics(session, current_user)
    elif report_type == "users":
        data = await get_users_analytics(session, current_user)
    elif report_type == "teams":
        data = await get_teams_analytics(session, current_user)
    elif report_type == "roles":
        data = await get_roles_analytics(session, current_user)

    # 这里可以实现实际的导出逻辑（如生成CSV、PDF等）
    # 暂时返回JSON数据

    return {
        "report_type": report_type,
        "exported_at": datetime.now().isoformat(),
        "data": data
    }