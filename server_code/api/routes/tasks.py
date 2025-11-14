from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, delete
from datetime import datetime
import os
import uuid
import json
from typing import Optional, List

from db.session import get_session
from db.models.task import Task, TaskAttachment, TaskAssignee, TaskComment
from db.models.user import User
from db.models.project import Project
from core.security import decode_token
from schemas.task import TaskOut, TaskCreate, TaskListResponse, TaskUpdate, TaskQuery, TaskCommentCreate
from schemas.project import AttachmentBrief
from core.notification_service import NotificationService
from api.deps.auth import require_permissions, get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])

# 任务状态选项
TASK_STATUSES = ["待处理", "进行中", "已完成", "已取消"]
TASK_PRIORITIES = ["低", "中", "高", "紧急"]

# 任务模型转换函数
def to_task_out(t: Task) -> TaskOut:
    # 获取负责人信息
    assignees = []
    if t.assignees:
        for assignee_rel in t.assignees:
            assignees.append({
                'id': assignee_rel.user.id,
                'nickname': assignee_rel.user.nickname,
                'username': assignee_rel.user.username
            })
    
    return TaskOut(
        id=t.id,
        title=t.title,
        description=t.description,
        status=t.status,
        priority=t.priority,
        assignees=assignees,
        project_id=t.project_id,
        project_name=t.project.name if t.project else None,
        created_by=t.created_by,
        created_by_name=t.creator.nickname or t.creator.username if t.creator else None,
        created_at=t.created_at,
        updated_at=t.updated_at,
        estimated_days=t.estimated_days,
        due_date=t.due_date,
    )


@router.get("/", response_model=TaskListResponse, dependencies=[Depends(require_permissions("tasks.view"))])
async def list_tasks(
    session: AsyncSession = Depends(get_session),
    page: int = 1,
    page_size: int = 10,
    project_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    exclude_status: Optional[str] = None,
):
    """分页查询任务列表"""
    filters = []
    if project_id:
        filters.append(Task.project_id == project_id)
    if assignee_id:
        # 筛选包含指定负责人的任务
        filters.append(Task.id.in_(
            select(TaskAssignee.task_id).where(TaskAssignee.user_id == assignee_id)
        ))
    if status:
        filters.append(Task.status == status)
    if priority:
        filters.append(Task.priority == priority)
    if exclude_status:
        # 解析逗号分隔的状态列表
        exclude_list = [s.strip() for s in exclude_status.split(',') if s.strip()]
        filters.append(Task.status.not_in(exclude_list))

    base_stmt = select(Task).where(and_(*filters)) if filters else select(Task)
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await session.execute(count_stmt)).scalar_one()

    stmt = base_stmt.order_by(Task.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    res = await session.execute(stmt)
    tasks = res.scalars().all()

    # 加载关联数据
    items = []
    for t in tasks:
        await session.refresh(t, ['assignees', 'project', 'creator'])
        # 加载负责人用户信息
        for assignee_rel in t.assignees:
            await session.refresh(assignee_rel, ['user'])
        items.append(to_task_out(t))

    return {"total": total, "items": items}


@router.get("/{task_id}", response_model=TaskOut, dependencies=[Depends(require_permissions("tasks.view"))])
async def get_task(task_id: int, session: AsyncSession = Depends(get_session)):
    """获取单个任务"""
    res = await session.execute(select(Task).where(Task.id == task_id))
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    await session.refresh(task, ['assignees', 'project', 'creator'])
    # 加载负责人用户信息
    for assignee_rel in task.assignees:
        await session.refresh(assignee_rel, ['user'])
    
    return to_task_out(task)


@router.post("/", response_model=TaskOut, dependencies=[Depends(require_permissions("tasks.create"))])
async def create_task(
    payload: TaskCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """创建新任务"""
    # 验证项目存在
    project_res = await session.execute(select(Project).where(Project.id == payload.project_id))
    project = project_res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=400, detail="项目不存在")

    # 验证状态和优先级
    if payload.status not in TASK_STATUSES:
        raise HTTPException(status_code=400, detail=f"无效的状态，可选值: {', '.join(TASK_STATUSES)}")
    if payload.priority not in TASK_PRIORITIES:
        raise HTTPException(status_code=400, detail=f"无效的优先级，可选值: {', '.join(TASK_PRIORITIES)}")

    # 验证负责人存在且属于项目成员
    if payload.assignee_ids:
        for assignee_id in payload.assignee_ids:
            assignee_res = await session.execute(select(User).where(User.id == assignee_id))
            assignee = assignee_res.scalar_one_or_none()
            if not assignee:
                raise HTTPException(status_code=400, detail=f"负责人 {assignee_id} 不存在")
            
            # 检查是否为项目成员（包括团队成员）
            from db.models.project import ProjectMember
            from db.models.team import TeamMember
            
            is_member = False
            
            # 检查是否为显式项目成员
            member_check = await session.execute(
                select(ProjectMember).where(
                    ProjectMember.project_id == payload.project_id,
                    ProjectMember.user_id == assignee_id
                )
            )
            if member_check.scalar_one_or_none():
                is_member = True
            
            # 如果不是显式成员，检查是否为团队成员
            if not is_member and project.team_id:
                team_member_check = await session.execute(
                    select(TeamMember).where(
                        TeamMember.team_id == project.team_id,
                        TeamMember.user_id == assignee_id
                    )
                )
                if team_member_check.scalar_one_or_none():
                    is_member = True
            
            if not is_member:
                raise HTTPException(status_code=400, detail=f"用户 {assignee.username} 不是项目成员，无法分配任务")

    # 计算截止日期
    due_date = None
    if payload.estimated_days:
        from datetime import timedelta
        due_date = datetime.utcnow() + timedelta(days=payload.estimated_days)

    task = Task(
        title=payload.title,
        description=payload.description,
        status=payload.status,
        priority=payload.priority,
        project_id=payload.project_id,
        created_by=current_user.id,
        estimated_days=payload.estimated_days,
        due_date=due_date,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)

    # 添加多个负责人
    if payload.assignee_ids:
        for assignee_id in payload.assignee_ids:
            task_assignee = TaskAssignee(
                task_id=task.id,
                user_id=assignee_id
            )
            session.add(task_assignee)
        await session.commit()

    await session.refresh(task, ['assignees', 'project', 'creator'])
    # 加载负责人用户信息
    for assignee_rel in task.assignees:
        await session.refresh(assignee_rel, ['user'])
    
    # 发送通知给负责人
    if payload.assignee_ids:
        await send_task_assignment_notifications(session, task, payload.assignee_ids, current_user)
    
    # 附件文件夹创建（按项目/任务分组）：projects/{project_id}/tasks/{task_id}
    project_folder = os.path.join(UPLOAD_DIR, "projects", str(task.project_id))
    task_folder = os.path.join(project_folder, "tasks", str(task.id))
    try:
        os.makedirs(task_folder, exist_ok=True)
    except Exception as e:
        # 记录但不阻止任务创建
        print(f"创建任务附件目录失败: {e}")

    return to_task_out(task)


@router.patch("/{task_id}", response_model=TaskOut, dependencies=[Depends(require_permissions("tasks.update"))])
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """更新任务"""
    res = await session.execute(select(Task).where(Task.id == task_id))
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 验证状态和优先级
    if payload.status and payload.status not in TASK_STATUSES:
        raise HTTPException(status_code=400, detail=f"无效的状态，可选值: {', '.join(TASK_STATUSES)}")
    if payload.priority and payload.priority not in TASK_PRIORITIES:
        raise HTTPException(status_code=400, detail=f"无效的优先级，可选值: {', '.join(TASK_PRIORITIES)}")

    # 验证负责人存在且为项目成员
    if payload.assignee_ids is not None:
        # 获取项目信息
        project_res = await session.execute(select(Project).where(Project.id == task.project_id))
        project = project_res.scalar_one_or_none()
        
        for assignee_id in payload.assignee_ids:
            assignee_res = await session.execute(select(User).where(User.id == assignee_id))
            assignee = assignee_res.scalar_one_or_none()
            if not assignee:
                raise HTTPException(status_code=400, detail=f"负责人 {assignee_id} 不存在")
            
            # 检查是否为项目成员（包括团队成员）
            from db.models.project import ProjectMember
            from db.models.team import TeamMember
            
            is_member = False
            
            # 检查是否为显式项目成员
            member_check = await session.execute(
                select(ProjectMember).where(
                    ProjectMember.project_id == task.project_id,
                    ProjectMember.user_id == assignee_id
                )
            )
            if member_check.scalar_one_or_none():
                is_member = True
            
            # 如果不是显式成员，检查是否为团队成员
            if not is_member and project and project.team_id:
                team_member_check = await session.execute(
                    select(TeamMember).where(
                        TeamMember.team_id == project.team_id,
                        TeamMember.user_id == assignee_id
                    )
                )
                if team_member_check.scalar_one_or_none():
                    is_member = True
            
            if not is_member:
                raise HTTPException(status_code=400, detail=f"用户 {assignee.username} 不是项目成员，无法分配任务")

    # 更新字段
    if payload.title is not None:
        task.title = payload.title
    if payload.description is not None:
        task.description = payload.description
    if payload.status is not None:
        task.status = payload.status
    if payload.priority is not None:
        task.priority = payload.priority
    if payload.estimated_days is not None:
        task.estimated_days = payload.estimated_days
        # 重新计算截止日期
        if payload.estimated_days:
            from datetime import timedelta
            task.due_date = datetime.utcnow() + timedelta(days=payload.estimated_days)
        else:
            task.due_date = None

    task.updated_at = datetime.utcnow()
    
    # 更新负责人
    if payload.assignee_ids is not None:
        # 删除现有的负责人关联
        await session.execute(delete(TaskAssignee).where(TaskAssignee.task_id == task_id))
        
        # 添加新的负责人关联
        for assignee_id in payload.assignee_ids:
            task_assignee = TaskAssignee(
                task_id=task_id,
                user_id=assignee_id
            )
            session.add(task_assignee)
    
    await session.commit()
    await session.refresh(task)

    await session.refresh(task, ['assignees', 'project', 'creator'])
    # 加载负责人用户信息
    for assignee_rel in task.assignees:
        await session.refresh(assignee_rel, ['user'])
    
    return to_task_out(task)


@router.delete("/{task_id}", dependencies=[Depends(require_permissions("tasks.delete"))])
async def delete_task(task_id: int, session: AsyncSession = Depends(get_session)):
    """删除任务"""
    res = await session.execute(select(Task).where(Task.id == task_id))
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 删除任务附件文件夹
    task_folder = os.path.join(UPLOAD_DIR, "projects", str(task.project_id), "tasks", str(task.id))
    if os.path.exists(task_folder):
        import shutil
        shutil.rmtree(task_folder, ignore_errors=True)

    await session.delete(task)
    await session.commit()
    return {"ok": True}


# 附件相关路由
UPLOAD_DIR = "uploads"


@router.get("/{task_id}/attachments", response_model=list[AttachmentBrief], dependencies=[Depends(require_permissions("tasks.view"))])
async def list_task_attachments(task_id: int, session: AsyncSession = Depends(get_session)):
    """获取任务附件列表"""
    # 验证任务存在并获取任务信息
    task_res = await session.execute(select(Task).where(Task.id == task_id))
    task = task_res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    res = await session.execute(
        select(TaskAttachment)
        .where(TaskAttachment.task_id == task_id)
        .order_by(TaskAttachment.uploaded_at.desc())
    )
    attachments = res.scalars().all()

    result = []
    for a in attachments:
        result.append(AttachmentBrief(
            id=a.id,
            filename=a.original_filename,
            url=f"/uploads/projects/{task.project_id}/tasks/{task_id}/{a.filename}",
            uploaded_at=a.uploaded_at,
            file_size=a.file_size,
            uploader_name=a.uploader.nickname or a.uploader.username if a.uploader else "未知"
        ))
    return result


@router.post("/{task_id}/attachments", response_model=AttachmentBrief, dependencies=[Depends(require_permissions("tasks.update"))])
async def upload_task_attachment(
    task_id: int,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    """上传任务附件"""
    # 验证任务存在并获取任务信息
    task_res = await session.execute(
        select(Task).where(Task.id == task_id)
    )
    task = task_res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 创建任务专属目录：projects/{project_id}/tasks/{task_id}/
    task_dir = os.path.join(UPLOAD_DIR, "projects", str(task.project_id), "tasks", str(task_id))
    try:
        os.makedirs(task_dir, exist_ok=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建任务目录失败: {str(e)}")

    # 生成唯一文件名
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(task_dir, unique_filename)

    # 保存文件
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        file_size = len(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")

    # 创建数据库记录
    attachment = TaskAttachment(
        task_id=task_id,
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        uploaded_by=1,  # TODO: 从认证中获取当前用户ID
    )
    session.add(attachment)
    await session.commit()
    await session.refresh(attachment)

    return AttachmentBrief(
        id=attachment.id,
        filename=attachment.original_filename,
        url=f"/uploads/projects/{task.project_id}/tasks/{task_id}/{attachment.filename}",
        uploaded_at=attachment.uploaded_at,
        file_size=attachment.file_size,
        uploader_name=attachment.uploader.nickname or attachment.uploader.username if attachment.uploader else "未知"
    )


@router.delete("/attachments/{attachment_id}", dependencies=[Depends(require_permissions("tasks.update"))])
async def delete_task_attachment(attachment_id: int, session: AsyncSession = Depends(get_session)):
    """删除任务附件"""
    res = await session.execute(select(TaskAttachment).where(TaskAttachment.id == attachment_id))
    attachment = res.scalar_one_or_none()
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")

    # 删除物理文件
    try:
        if os.path.exists(attachment.file_path):
            os.remove(attachment.file_path)
    except Exception as e:
        print(f"删除文件失败: {e}")  # 不抛出错误，继续删除数据库记录

    # 删除数据库记录
    await session.delete(attachment)
    await session.commit()
    return {"ok": True}


# 获取项目成员列表（用于任务负责人选择）- 通过团队成员接口获取
# 此接口已移除，请使用 /teams/{team_id}/members 接口
# 通知相关函数
async def send_task_assignment_notifications(session: AsyncSession, task: Task, assignee_ids: List[int], assigner: User):
    """发送任务分配通知"""
    await NotificationService.create_task_assigned_notifications(
        session=session,
        assignee_ids=assignee_ids,
        assigner=assigner,
        task=task
    )

# 任务评论相关API
@router.get("/{task_id}/comments", response_model=dict, dependencies=[Depends(require_permissions("tasks.view"))])
async def get_task_comments(
    task_id: int,
    page: int = 1,
    page_size: int = 20,
    session: AsyncSession = Depends(get_session)
):
    """获取任务评论列表"""
    # 验证任务存在
    task_res = await session.execute(select(Task).where(Task.id == task_id))
    if not task_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="任务不存在")

    # 获取评论总数
    count_res = await session.execute(
        select(func.count(TaskComment.id)).where(TaskComment.task_id == task_id)
    )
    total = count_res.scalar()

    # 获取评论列表
    comments_res = await session.execute(
        select(TaskComment).where(TaskComment.task_id == task_id)
        .order_by(TaskComment.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    comments = comments_res.scalars().all()

    # 格式化评论数据
    comment_list = []
    for comment in comments:
        comment_list.append({
            "id": comment.id,
            "content": comment.content,
            "mentioned_users": json.loads(comment.mentioned_users) if comment.mentioned_users else [],
            "created_at": comment.created_at.isoformat(),
            "user": {
                "id": comment.user.id,
                "username": comment.user.username,
                "nickname": comment.user.nickname
            }
        })

    return {
        "items": comment_list,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/{task_id}/comments", response_model=dict, dependencies=[Depends(require_permissions("tasks.view"))])
async def create_task_comment(
    task_id: int,
    payload: TaskCommentCreate,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """创建任务评论"""
    # 验证任务存在
    task_res = await session.execute(select(Task).where(Task.id == task_id))
    if not task_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="任务不存在")

    # 将mentioned_users转换为JSON字符串存储
    import json
    mentioned_users_json = json.dumps(payload.mentioned_users) if payload.mentioned_users else None

    # 创建评论
    comment = TaskComment(
        task_id=task_id,
        user_id=current_user.id,
        content=payload.content,
        mentioned_users=mentioned_users_json
    )
    session.add(comment)
    await session.commit()
    await session.refresh(comment)

    return {
        "id": comment.id,
        "content": comment.content,
        "mentioned_users": payload.mentioned_users,
        "created_at": comment.created_at.isoformat(),
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "nickname": current_user.nickname
        }
    }


@router.delete("/{task_id}/comments/{comment_id}", dependencies=[Depends(require_permissions("tasks.update"))])
async def delete_task_comment(
    task_id: int,
    comment_id: int,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """删除任务评论"""
    # 获取评论
    comment_res = await session.execute(
        select(TaskComment).where(
            and_(TaskComment.id == comment_id, TaskComment.task_id == task_id)
        )
    )
    comment = comment_res.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    # 检查权限（只能删除自己的评论或有权限的用户）
    if comment.user_id != current_user.id:
        # 这里可以添加管理员权限检查
        raise HTTPException(status_code=403, detail="无权限删除此评论")

    # 删除评论
    await session.delete(comment)
    await session.commit()

    return {"ok": True}