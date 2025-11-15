"""项目路由：列表、创建、详情。"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, delete, func
from sqlalchemy.orm import selectinload
from datetime import date, timedelta, datetime
import json
import os
import uuid
import shutil

from db.session import get_session
from db.models.project import Project, ProjectAttachment, ProjectComment, ProjectTimeline, ProjectMember, ProjectMilestone
from db.models.user import User
from db.models.role import Role
from db.models.user_role import UserRole
from db.models.team import TeamMember
from db.models.task import Task
from core.notification_service import NotificationService
from api.deps.auth import require_permissions, get_current_user
from schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectBrief,
    ProjectDetail,
    AttachmentBrief,
    CommentOut,
    CommentCreate,
    TimelineItem,
    MemberOut,
    MilestoneCreate,
    MilestoneUpdate,
    MilestoneOut,
)

router = APIRouter(prefix="/projects", tags=["projects"])

# 文件上传目录（相对于项目根目录）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")


@router.get("/", response_model=list[ProjectBrief], dependencies=[Depends(require_permissions("projects.view"))])
async def list_projects(session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    # 检查用户是否为超级管理员
    user_roles_q = await session.execute(
        select(Role).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == current_user.id)
    )
    user_roles = user_roles_q.scalars().all()
    is_superadmin = any(role.is_superadmin for role in user_roles) or (
        current_user.role_id and (
            await session.execute(select(Role).where(Role.id == current_user.role_id))
        ).scalar_one_or_none().is_superadmin
    )
    
    base_query = select(Project)
    if not is_superadmin:
        # 普通用户只能看到：
        # 1. 自己作为负责人的项目
        # 2. 自己作为项目成员的项目  
        # 3. 自己所属团队的项目
        from db.models.team import TeamMember
        base_query = base_query.where(
            or_(
                Project.owner_id == current_user.id,
                Project.id.in_(
                    select(ProjectMember.project_id).where(ProjectMember.user_id == current_user.id)
                ),
                Project.team_id.in_(
                    select(TeamMember.team_id).where(TeamMember.user_id == current_user.id)
                )
            )
        )
    
    q = await session.execute(base_query.order_by(Project.id.desc()))
    projects = q.scalars().all()
    
    # 为每个项目计算任务数量
    result = []
    for project in projects:
        # 计算总任务数
        total_tasks_q = await session.execute(
            select(Task).where(Task.project_id == project.id)
        )
        total_tasks = len(total_tasks_q.scalars().all())
        
        # 计算未完成任务数（状态不为"已完成"且不为"已取消"的任务）
        incomplete_tasks_q = await session.execute(
            select(Task).where(Task.project_id == project.id, Task.status != "已完成", Task.status != "已取消")
        )
        incomplete_tasks = len(incomplete_tasks_q.scalars().all())
        
        # 获取项目负责人列表
        leaders_q = await session.execute(
            select(ProjectMember.user_id).where(
                ProjectMember.project_id == project.id,
                ProjectMember.role == "负责人"
            )
        )
        leader_ids = [row[0] for row in leaders_q]
        
        # 创建带有任务统计的项目对象
        project_dict = {
            "id": project.id,
            "name": project.name,
            "status": project.status,
            "leader_ids": leader_ids,
            "team_id": project.team_id,
            "development_days": project.development_days,
            "start_date": project.start_date,
            "end_date": project.end_date,
            "created_at": project.created_at,
            "total_tasks": total_tasks,
            "incomplete_tasks": incomplete_tasks,
        }
        result.append(project_dict)
    
    return result


@router.post("/", response_model=ProjectDetail, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permissions("projects.create"))])
async def create_project(payload: ProjectCreate, session: AsyncSession = Depends(get_session)):
    # 自动计算开始日期和结束日期
    start_date = payload.start_date or date.today()  # 默认今天开始
    end_date = payload.end_date
    
    # 如果提供了开发周期，根据周期计算结束日期
    if payload.development_days and payload.development_days > 0:
        end_date = start_date + timedelta(days=payload.development_days)
    
    project = Project(
        name=payload.name,
        description=payload.description,
        status=payload.status or "planned",
        team_id=payload.team_id,
        development_days=payload.development_days,
        start_date=start_date,
        end_date=end_date,
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)
    
    # 如果指定了项目负责人，批量创建项目成员记录
    if payload.leader_ids:
        from db.models.project import ProjectMember
        for leader_id in payload.leader_ids:
            member = ProjectMember(
                project_id=project.id,
                user_id=leader_id,
                role="负责人"
            )
            session.add(member)
        await session.commit()
        
        # 给项目负责人发送通知
        await NotificationService.create_project_member_added_notifications(
            session, payload.leader_ids, None, project
        )
    
    # 如果指定了团队，给团队成员发送通知
    if project.team_id:
        from db.models.team import TeamMember
        # 获取团队成员
        team_members_q = await session.execute(
            select(TeamMember.user_id).where(TeamMember.team_id == project.team_id)
        )
        team_member_ids = [row[0] for row in team_members_q]
        
        if team_member_ids:
            await NotificationService.create_team_project_assigned_notifications(
                session, team_member_ids, project
            )
    
    # 创建项目专属目录
    project_dir = os.path.join(UPLOAD_DIR, "projects", str(project.id))
    tasks_dir = os.path.join(project_dir, "tasks")
    try:
        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(tasks_dir, exist_ok=True)
    except Exception as e:
        # 记录错误但不影响项目创建
        print(f"创建项目目录失败: {str(e)}")
    
    return project


@router.get("/{project_id}", response_model=ProjectDetail, dependencies=[Depends(require_permissions("projects.view"))])
async def get_project(project_id: int, session: AsyncSession = Depends(get_session)):
    q = await session.execute(select(Project).where(Project.id == project_id))
    project = q.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    # 获取项目负责人列表
    leaders_q = await session.execute(
        select(ProjectMember.user_id).where(
            ProjectMember.project_id == project_id,
            ProjectMember.role == "负责人"
        )
    )
    leader_ids = [row[0] for row in leaders_q]
    
    # 计算任务统计
    total_tasks_q = await session.execute(
        select(Task).where(Task.project_id == project_id)
    )
    total_tasks = len(total_tasks_q.scalars().all())
    
    incomplete_tasks_q = await session.execute(
        select(Task).where(Task.project_id == project_id, Task.status != "已完成", Task.status != "已取消")
    )
    incomplete_tasks = len(incomplete_tasks_q.scalars().all())
    
    # 手动构造返回对象
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "leader_ids": leader_ids,
        "team_id": project.team_id,
        "development_days": project.development_days,
        "start_date": project.start_date,
        "end_date": project.end_date,
        "created_at": project.created_at,
        "total_tasks": total_tasks,
        "incomplete_tasks": incomplete_tasks,
    }


@router.put("/{project_id}", response_model=ProjectDetail, dependencies=[Depends(require_permissions("projects.update"))])
async def update_project(
    project_id: int, 
    payload: ProjectUpdate, 
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # 获取项目
    q = await session.execute(select(Project).where(Project.id == project_id))
    project = q.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    # 权限检查：只有项目负责人或管理员可以更新
    is_admin = False
    if current_user.role_id:
        role_q = await session.execute(select(Role).where(Role.id == current_user.role_id))
        user_role = role_q.scalar_one_or_none()
        is_admin = user_role and user_role.name in ["管理员", "超级管理员"]
    
    # 检查是否是项目负责人之一
    from db.models.project import ProjectMember
    leader_q = await session.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
            ProjectMember.role == "负责人"
        )
    )
    is_leader = leader_q.scalar_one_or_none() is not None
    
    if not (is_admin or is_leader):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权修改此项目")
    
    # 记录原始team_id，用于检查是否变化
    original_team_id = project.team_id
    
    # 只更新提供的字段
    if payload.name is not None:
        project.name = payload.name
    if payload.description is not None:
        project.description = payload.description
    if payload.status is not None:
        project.status = payload.status
    if payload.leader_ids is not None:
        # 删除旧的项目负责人记录
        await session.execute(
            delete(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.role == "负责人"
            )
        )
        # 添加新的项目负责人记录
        for leader_id in payload.leader_ids:
            member = ProjectMember(
                project_id=project_id,
                user_id=leader_id,
                role="负责人"
            )
            session.add(member)
    if payload.team_id is not None:
        project.team_id = payload.team_id
    if payload.development_days is not None:
        project.development_days = payload.development_days
    if payload.start_date is not None:
        project.start_date = payload.start_date
    
    # 重新计算结束日期
    if payload.development_days is not None and project.development_days and project.development_days > 0 and project.start_date:
        project.end_date = project.start_date + timedelta(days=project.development_days)
    elif payload.end_date is not None:
        project.end_date = payload.end_date
    
    await session.commit()
    await session.refresh(project)
    
    # 如果团队发生了变化，给新团队成员发送通知
    if payload.team_id is not None and payload.team_id != original_team_id and payload.team_id is not None:
        from db.models.team import TeamMember
        # 获取新团队成员
        team_members_q = await session.execute(
            select(TeamMember.user_id).where(TeamMember.team_id == payload.team_id)
        )
        team_member_ids = [row[0] for row in team_members_q]
        
        if team_member_ids:
            await NotificationService.create_team_project_assigned_notifications(
                session, team_member_ids, project
            )
    
    return project


@router.delete("/{project_id}", dependencies=[Depends(require_permissions("projects.delete"))])
async def delete_project(
    project_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """删除项目"""
    # 获取项目
    q = await session.execute(select(Project).where(Project.id == project_id))
    project = q.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    # 权限检查：只有项目负责人或管理员可以删除
    is_admin = False
    if current_user.role_id:
        role_q = await session.execute(select(Role).where(Role.id == current_user.role_id))
        user_role = role_q.scalar_one_or_none()
        is_admin = user_role and user_role.name in ["管理员", "超级管理员"]
    
    # 检查是否是项目负责人之一
    from db.models.project import ProjectMember
    leader_q = await session.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
            ProjectMember.role == "负责人"
        )
    )
    is_leader = leader_q.scalar_one_or_none() is not None
    
    if not (is_admin or is_leader):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除此项目")
    
    # 删除项目相关的物理文件（整个项目目录）
    project_dir = os.path.join(UPLOAD_DIR, "projects", str(project_id))
    if os.path.exists(project_dir):
        try:
            shutil.rmtree(project_dir)
        except Exception as e:
            # 记录错误但继续删除数据库记录
            print(f"删除项目目录失败: {str(e)}")
    
    # 删除项目（级联删除会处理相关数据）
    await session.delete(project)
    await session.commit()
    return {"ok": True}


@router.get("/{project_id}/attachments", response_model=list[AttachmentBrief], dependencies=[Depends(require_permissions("projects.view"))])
async def list_attachments(project_id: int, session: AsyncSession = Depends(get_session)):
    q = await session.execute(
        select(ProjectAttachment).where(ProjectAttachment.project_id == project_id).order_by(ProjectAttachment.id.desc())
    )
    attachments = q.scalars().all()
    
    # 填充上传者姓名
    result = []
    for att in attachments:
        att_dict = {
            'id': att.id,
            'filename': att.filename,
            'url': att.url,
            'file_size': att.file_size,
            'uploaded_by': att.uploaded_by,
            'uploaded_at': att.uploaded_at,
            'uploader_name': None
        }
        
        # 获取上传者信息
        if att.uploaded_by:
            user_q = await session.execute(select(User).where(User.id == att.uploaded_by))
            user = user_q.scalar_one_or_none()
            if user:
                att_dict['uploader_name'] = user.nickname or user.username
        
        result.append(att_dict)
    
    return result


@router.get("/{project_id}/comments", response_model=dict, dependencies=[Depends(require_permissions("projects.view"))])
async def list_comments(
    project_id: int,
    page: int = 1,
    page_size: int = 20,
    session: AsyncSession = Depends(get_session)
):
    """获取项目评论列表"""
    # 验证项目存在
    project_res = await session.execute(select(Project).where(Project.id == project_id))
    if not project_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="项目不存在")

    # 获取评论总数
    count_res = await session.execute(
        select(func.count(ProjectComment.id)).where(ProjectComment.project_id == project_id)
    )
    total = count_res.scalar()

    # 获取评论列表
    comments_res = await session.execute(
        select(ProjectComment).where(ProjectComment.project_id == project_id)
        .order_by(ProjectComment.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    comments = comments_res.scalars().all()

    # 填充用户信息
    comment_list = []
    for c in comments:
        # 先解析 mentioned_users
        mentioned_list = []
        if c.mentioned_users:
            try:
                mentioned_list = json.loads(c.mentioned_users)
            except:
                mentioned_list = []

        # 创建字典
        comment_data = {
            'id': c.id,
            'user_id': c.user_id,
            'content': c.content,
            'mentioned_users': mentioned_list,
            'created_at': c.created_at.isoformat() if c.created_at else None,
            'user_nickname': None,
            'user_username': None,
            'user_role_name': None
        }

        # 获取评论者信息
        if c.user_id:
            user_q = await session.execute(select(User).where(User.id == c.user_id))
            user = user_q.scalar_one_or_none()
            if user:
                comment_data['user_nickname'] = user.nickname
                comment_data['user_username'] = user.username

                # 获取角色名称
                if user.role_id:
                    role_q = await session.execute(select(Role).where(Role.id == user.role_id))
                    role = role_q.scalar_one_or_none()
                    if role:
                        comment_data['user_role_name'] = role.name

        comment_list.append(comment_data)

    return {
        "items": comment_list,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/{project_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def add_comment(project_id: int, payload: CommentCreate, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    # 检查项目是否存在
    project_q = await session.execute(select(Project).where(Project.id == project_id))
    project = project_q.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    # 权限检查：项目负责人、团队成员或超级管理员可以评论
    has_permission = False
    
    # 检查是否是超级管理员
    user_roles_q = await session.execute(
        select(Role).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user.id)
    )
    user_roles = user_roles_q.scalars().all()
    is_superadmin = any(role.is_superadmin for role in user_roles) or (
        user.role_id and (
            await session.execute(select(Role).where(Role.id == user.role_id))
        ).scalar_one_or_none().is_superadmin
    )
    
    if is_superadmin:
        has_permission = True
    else:
        # 检查是否是项目负责人
        if project.owner_id == user.id:
            has_permission = True
        
        # 如果不是负责人，检查是否是团队成员
        if not has_permission and project.team_id:
            team_member_q = await session.execute(
                select(TeamMember).where(
                    TeamMember.team_id == project.team_id,
                    TeamMember.user_id == user.id
                )
            )
            if team_member_q.scalar_one_or_none():
                has_permission = True
    
    if not has_permission:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有项目负责人、团队成员或超级管理员可以发表评论")
    
    # 保存被@用户的ID列表
    mentioned_users_json = None
    if payload.mentioned_user_ids:
        mentioned_users_json = json.dumps(payload.mentioned_user_ids)
    
    c = ProjectComment(
        project_id=project_id, 
        user_id=user.id, 
        content=payload.content,
        mentioned_users=mentioned_users_json
    )
    session.add(c)
    await session.commit()
    await session.refresh(c)
    
    # 创建@提及通知
    if payload.mentioned_user_ids:
        await NotificationService.create_mention_notifications(
            session=session,
            mentioned_user_ids=payload.mentioned_user_ids,
            mentioner=user,
            project_id=project_id,
            comment_content=payload.content
        )
    
    # 手动构建返回字典，解析 JSON 字符串
    mentioned_list = []
    if c.mentioned_users:
        try:
            mentioned_list = json.loads(c.mentioned_users)
        except:
            mentioned_list = []
    
    comment_dict = {
        'id': c.id,
        'project_id': c.project_id,
        'user_id': c.user_id,
        'content': c.content,
        'mentioned_users': mentioned_list,
        'created_at': c.created_at,
        'user_nickname': user.nickname,
        'user_username': user.username,
        'user_role_name': None
    }
    
    if user.role_id:
        role_q = await session.execute(select(Role).where(Role.id == user.role_id))
        role = role_q.scalar_one_or_none()
        if role:
            comment_dict['user_role_name'] = role.name
    
    return comment_dict


@router.delete("/comments/{comment_id}", dependencies=[Depends(require_permissions("projects.update"))])
async def delete_comment(
    comment_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # 获取评论
    q = await session.execute(select(ProjectComment).where(ProjectComment.id == comment_id))
    comment = q.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评论不存在")
    
    # 权限检查：管理员或评论作者可以删除
    is_admin = False
    if current_user.role_id:
        role_q = await session.execute(select(Role).where(Role.id == current_user.role_id))
        user_role = role_q.scalar_one_or_none()
        is_admin = user_role and user_role.name in ["管理员", "超级管理员"]
    
    is_author = comment.user_id == current_user.id
    
    if not (is_admin or is_author):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除此评论")
    
    await session.delete(comment)
    await session.commit()
    return {"message": "评论删除成功"}


@router.put("/comments/{comment_id}", response_model=CommentOut, dependencies=[Depends(require_permissions("projects.update"))])
async def update_comment(
    comment_id: int,
    payload: CommentCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # 获取评论
    q = await session.execute(select(ProjectComment).where(ProjectComment.id == comment_id))
    comment = q.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评论不存在")
    
    # 权限检查：只有评论作者可以编辑
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只能编辑自己的评论")
    
    # 更新评论
    comment.content = payload.content
    if payload.mentioned_user_ids:
        comment.mentioned_users = json.dumps(payload.mentioned_user_ids)
    else:
        comment.mentioned_users = None
    
    await session.commit()
    await session.refresh(comment)
    
    # 创建@提及通知
    if payload.mentioned_user_ids:
        await NotificationService.create_mention_notifications(
            session=session,
            mentioned_user_ids=payload.mentioned_user_ids,
            mentioner=current_user,
            project_id=comment.project_id,
            comment_content=payload.content
        )
    
    # 返回时填充用户信息
    comment_dict = {
        'id': comment.id,
        'user_id': comment.user_id,
        'content': comment.content,
        'mentioned_users': payload.mentioned_user_ids or [],
        'created_at': comment.created_at,
        'user_nickname': current_user.nickname,
        'user_username': current_user.username,
        'user_role_name': None
    }
    
    if current_user.role_id:
        role_q = await session.execute(select(Role).where(Role.id == current_user.role_id))
        role = role_q.scalar_one_or_none()
        if role:
            comment_dict['user_role_name'] = role.name
    
    return CommentOut(**comment_dict)


@router.get("/{project_id}/timeline", response_model=list[TimelineItem], dependencies=[Depends(require_permissions("projects.view"))])
async def list_timeline(project_id: int, session: AsyncSession = Depends(get_session)):
    q = await session.execute(
        select(ProjectTimeline).where(ProjectTimeline.project_id == project_id).order_by(ProjectTimeline.occurred_at.desc())
    )
    return q.scalars().all()


@router.post("/{project_id}/attachments", response_model=AttachmentBrief, dependencies=[Depends(require_permissions("projects.update"))])
async def upload_attachment(
    project_id: int, 
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # 检查项目是否存在
    project_q = await session.execute(select(Project).where(Project.id == project_id))
    project = project_q.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    # 生成唯一文件名
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    
    # 使用项目专属目录
    project_dir = os.path.join(UPLOAD_DIR, "projects", str(project_id))
    os.makedirs(project_dir, exist_ok=True)
    file_path = os.path.join(project_dir, unique_filename)
    
    # 保存文件并获取文件大小
    file_size = 0
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        file_size = os.path.getsize(file_path)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"文件保存失败: {str(e)}")
    
    # 创建数据库记录
    attachment = ProjectAttachment(
        project_id=project_id,
        filename=file.filename,  # 保存原始文件名
        url=f"/uploads/projects/{project_id}/{unique_filename}",  # 包含项目ID的URL路径
        file_size=file_size,  # 保存文件大小
        uploaded_by=current_user.id,
        uploaded_at=datetime.now()
    )
    session.add(attachment)
    await session.commit()
    await session.refresh(attachment)
    
    return attachment


@router.get("/attachments/{attachment_id}/download", dependencies=[Depends(require_permissions("projects.view"))])
async def download_attachment(
    attachment_id: int,
    session: AsyncSession = Depends(get_session)
):
    # 获取附件信息
    q = await session.execute(select(ProjectAttachment).where(ProjectAttachment.id == attachment_id))
    attachment = q.scalar_one_or_none()
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="附件不存在")
    
    # 从URL提取文件路径
    # URL格式: /uploads/projects/{project_id}/{unique_filename}
    url_parts = attachment.url.split('/')
    if len(url_parts) >= 4 and url_parts[-3] == 'projects':
        project_id_str = url_parts[-2]
        filename = url_parts[-1]
        file_path = os.path.join(UPLOAD_DIR, "projects", project_id_str, filename)
    else:
        # 兼容旧格式
        unique_filename = attachment.url.split('/')[-1]
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")
    
    # 返回文件
    return FileResponse(
        path=file_path,
        filename=attachment.filename,  # 使用原始文件名
        media_type='application/octet-stream'
    )


@router.delete("/attachments/{attachment_id}", dependencies=[Depends(require_permissions("projects.update"))])
async def delete_attachment(
    attachment_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # 获取附件信息
    q = await session.execute(select(ProjectAttachment).where(ProjectAttachment.id == attachment_id))
    attachment = q.scalar_one_or_none()
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="附件不存在")
    
    # 获取项目信息进行权限检查
    project_q = await session.execute(select(Project).where(Project.id == attachment.project_id))
    project = project_q.scalar_one_or_none()
    
    # 权限检查：只有项目负责人、上传者本人或管理员可以删除
    is_admin = False
    if current_user.role_id:
        role_q = await session.execute(select(Role).where(Role.id == current_user.role_id))
        user_role = role_q.scalar_one_or_none()
        is_admin = user_role and user_role.name == "管理员"
    
    is_owner = project and project.owner_id == current_user.id
    is_uploader = attachment.uploaded_by == current_user.id
    
    if not (is_admin or is_owner or is_uploader):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除此附件")
    
    # 删除物理文件
    # URL格式: /uploads/projects/{project_id}/{unique_filename}
    url_parts = attachment.url.split('/')
    if len(url_parts) >= 4 and url_parts[-3] == 'projects':
        project_id_str = url_parts[-2]
        filename = url_parts[-1]
        file_path = os.path.join(UPLOAD_DIR, "projects", project_id_str, filename)
    else:
        # 兼容旧格式
        unique_filename = attachment.url.split('/')[-1]
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            # 记录错误但继续删除数据库记录
            print(f"删除文件失败: {str(e)}")
    
    # 删除数据库记录
    await session.delete(attachment)
    await session.commit()
    
    return {"message": "附件删除成功"}


@router.get("/{project_id}/members", response_model=list[MemberOut], dependencies=[Depends(require_permissions("projects.view"))])
async def list_project_members(project_id: int, session: AsyncSession = Depends(get_session)):
    """获取项目成员列表"""
    # 验证项目存在
    project_q = await session.execute(select(Project).where(Project.id == project_id))
    project = project_q.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    result = []
    
    # 获取所有相关用户的ID
    user_ids = set()
    
    # 获取通过ProjectMember记录的成员
    explicit_members_q = await session.execute(
        select(ProjectMember.user_id).where(ProjectMember.project_id == project_id)
    )
    explicit_user_ids = [row[0] for row in explicit_members_q]
    user_ids.update(explicit_user_ids)
    
    # 获取通过团队关系的成员
    if project.team_id:
        team_members_q = await session.execute(
            select(TeamMember.user_id).where(TeamMember.team_id == project.team_id)
        )
        team_user_ids = [row[0] for row in team_members_q]
        user_ids.update(team_user_ids)
    
    # 为每个用户获取详细信息和角色
    for user_id in user_ids:
        user_q = await session.execute(select(User).where(User.id == user_id))
        user = user_q.scalar_one_or_none()
        if not user:
            continue
            
        # 获取用户的所有角色
        role_names = []
        
        # 获取用户主角色（通过user.role_id）
        if user.role_id:
            main_role_q = await session.execute(select(Role).where(Role.id == user.role_id))
            main_role = main_role_q.scalar_one_or_none()
            if main_role:
                role_names.append(main_role.name)
        
        # 获取用户额外角色（通过UserRole表）
        user_roles_q = await session.execute(
            select(Role).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user_id)
        )
        extra_roles = user_roles_q.scalars().all()
        for role in extra_roles:
            if role.name not in role_names:  # 避免重复
                role_names.append(role.name)
        
        # 检查是否是项目负责人
        is_leader = False
        if user_id in explicit_user_ids:
            leader_q = await session.execute(
                select(ProjectMember).where(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == user_id,
                    ProjectMember.role == "负责人"
                )
            )
            is_leader = leader_q.scalar_one_or_none() is not None
        
        # 获取加入时间
        joined_at = None
        if user_id in explicit_user_ids:
            member_q = await session.execute(
                select(ProjectMember).where(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == user_id
                )
            )
            member = member_q.scalar_one_or_none()
            joined_at = member.joined_at if member else None
        elif project.team_id:
            team_member_q = await session.execute(
                select(TeamMember).where(
                    TeamMember.team_id == project.team_id,
                    TeamMember.user_id == user_id
                )
            )
            team_member = team_member_q.scalar_one_or_none()
            joined_at = team_member.created_at if team_member else None
        
        result.append({
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "email": None,  # User model doesn't have email field
            "roles": role_names,  # 多个角色
            "joined_at": joined_at,
            "online": user.online,
            "is_leader": is_leader  # 是否是项目负责人
        })
    
    return result


# 里程碑相关路由
@router.get("/{project_id}/milestones", response_model=list[MilestoneOut], dependencies=[Depends(require_permissions("projects.view"))])
async def list_milestones(project_id: int, session: AsyncSession = Depends(get_session)):
    """获取项目里程碑列表"""
    q = await session.execute(
        select(ProjectMilestone)
        .where(ProjectMilestone.project_id == project_id)
        .options(selectinload(ProjectMilestone.creator))
        .order_by(ProjectMilestone.created_at.desc())
    )
    return q.scalars().all()


@router.post("/{project_id}/milestones", response_model=MilestoneOut, dependencies=[Depends(require_permissions("projects.update"))])
async def create_milestone(project_id: int, payload: MilestoneCreate, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """创建项目里程碑"""
    # 验证项目存在
    project_q = await session.execute(select(Project).where(Project.id == project_id))
    project = project_q.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    milestone = ProjectMilestone(
        project_id=project_id,
        created_by=current_user.id,
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        status=payload.status,
    )
    session.add(milestone)
    await session.commit()
    await session.refresh(milestone)
    return milestone


@router.put("/milestones/{milestone_id}", response_model=MilestoneOut, dependencies=[Depends(require_permissions("projects.update"))])
async def update_milestone(milestone_id: int, payload: MilestoneUpdate, session: AsyncSession = Depends(get_session)):
    """更新项目里程碑"""
    q = await session.execute(select(ProjectMilestone).where(ProjectMilestone.id == milestone_id))
    milestone = q.scalar_one_or_none()
    if not milestone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="里程碑不存在")
    
    # 更新字段
    if payload.title is not None:
        milestone.title = payload.title
    if payload.description is not None:
        milestone.description = payload.description
    if payload.due_date is not None:
        milestone.due_date = payload.due_date
    if payload.status is not None:
        milestone.status = payload.status
        # 如果状态改为完成，设置完成时间
        if payload.status == "completed" and milestone.completed_at is None:
            milestone.completed_at = datetime.utcnow()
        elif payload.status != "completed":
            milestone.completed_at = None
    
    milestone.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(milestone)
    return milestone


@router.delete("/milestones/{milestone_id}", dependencies=[Depends(require_permissions("projects.update"))])
async def delete_milestone(milestone_id: int, session: AsyncSession = Depends(get_session)):
    """删除项目里程碑"""
    q = await session.execute(select(ProjectMilestone).where(ProjectMilestone.id == milestone_id))
    milestone = q.scalar_one_or_none()
    if not milestone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="里程碑不存在")
    
    await session.delete(milestone)
    await session.commit()
    return {"message": "里程碑删除成功"}
