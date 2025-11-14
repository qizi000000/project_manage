"""通知服务（中文注释）。

提供创建和管理通知的功能。
"""

import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from db.models.notification import Notification, NotificationType
from db.models.user import User
from db.models.project import Project
from db.models.task import Task
from schemas.notification import NotificationCreate
from api.routes.ws import manager


def clean_html_tags(text: str) -> str:
    """清理HTML标签，保留纯文本内容"""
    # 移除HTML标签
    clean_text = re.sub(r'<[^>]+>', '', text)
    # 清理多余的空白字符
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text


class NotificationService:
    """通知服务类"""

    @staticmethod
    async def send_ws_notification(user_id: int, notification_data: dict):
        """通过WebSocket发送通知"""
        websocket = manager.get(user_id)
        if websocket:
            try:
                await websocket.send_json({
                    "type": "notification",
                    "data": notification_data
                })
            except Exception as e:
                print(f"发送WebSocket通知失败: {e}")

    @staticmethod
    async def create_notification(
        session: AsyncSession,
        notification: NotificationCreate
    ) -> Notification:
        """创建通知"""
        db_notification = Notification(
            user_id=notification.user_id,
            type=notification.type,
            title=notification.title,
            content=notification.content,
            related_id=notification.related_id,
            related_type=notification.related_type
        )
        session.add(db_notification)
        await session.commit()
        await session.refresh(db_notification)
        
        # 通过WebSocket发送实时通知
        notification_data = {
            "id": db_notification.id,
            "type": db_notification.type.value,
            "title": db_notification.title,
            "content": db_notification.content,
            "related_id": db_notification.related_id,
            "related_type": db_notification.related_type,
            "created_at": db_notification.created_at.isoformat(),
            "is_read": False
        }
        await NotificationService.send_ws_notification(notification.user_id, notification_data)
        
        return db_notification

    @staticmethod
    async def create_mention_notifications(
        session: AsyncSession,
        mentioned_user_ids: List[int],
        mentioner: User,
        project_id: int,
        comment_content: str
    ):
        """创建@提及通知"""
        if not mentioned_user_ids:
            return

        # 获取项目信息
        project_stmt = select(Project).where(Project.id == project_id)
        project = (await session.execute(project_stmt)).scalar_one_or_none()
        if not project:
            return

        for user_id in mentioned_user_ids:
            if user_id == mentioner.id:  # 不给自己发通知
                continue

            notification = NotificationCreate(
                user_id=user_id,
                type=NotificationType.MENTION,
                title=f"你在项目「{project.name}」中被提及",
                content=f"{mentioner.nickname or mentioner.username} 在评论中提及了你: {clean_html_tags(comment_content)[:100]}{'...' if len(clean_html_tags(comment_content)) > 100 else ''}",
                related_id=project_id,
                related_type="project"
            )
            await NotificationService.create_notification(session, notification)

    @staticmethod
    async def create_task_assigned_notifications(
        session: AsyncSession,
        assignee_ids: List[int],
        assigner: User,
        task: Task
    ):
        """创建任务分配通知"""
        if not assignee_ids:
            return

        for user_id in assignee_ids:
            if user_id == assigner.id:  # 不给自己发通知
                continue

            notification = NotificationCreate(
                user_id=user_id,
                type=NotificationType.TASK_ASSIGNED,
                title=f"你被分配了新任务",
                content=f"{assigner.nickname or assigner.username} 给你分配了任务: {task.title}",
                related_id=task.id,
                related_type="task"
            )
            await NotificationService.create_notification(session, notification)

    @staticmethod
    async def create_team_member_added_notifications(
        session: AsyncSession,
        new_member_ids: List[int],
        adder: User,
        team_id: int,
        team_name: str
    ):
        """创建团队成员添加通知"""
        for user_id in new_member_ids:
            if user_id == adder.id:  # 不给自己发通知
                continue

            notification = NotificationCreate(
                user_id=user_id,
                type=NotificationType.TEAM_INVITE,
                title=f"你被添加到团队「{team_name}」",
                content=f"{adder.nickname or adder.username} 将你添加到了团队「{team_name}」",
                related_id=team_id,
                related_type="team"
            )
            await NotificationService.create_notification(session, notification)

    @staticmethod
    async def create_project_member_added_notifications(
        session: AsyncSession,
        new_member_ids: List[int],
        adder: User,
        project: Project
    ):
        """创建项目成员添加通知"""
        for user_id in new_member_ids:
            if adder and user_id == adder.id:  # 不给自己发通知
                continue

            if adder:
                # 手动添加成员的通知
                notification = NotificationCreate(
                    user_id=user_id,
                    type=NotificationType.PROJECT_ASSIGNED,
                    title=f"你被分配到项目「{project.name}」",
                    content=f"{adder.nickname or adder.username} 将你添加到了项目「{project.name}」",
                    related_id=project.id,
                    related_type="project"
                )
            else:
                # 项目创建时自动分配的通知
                notification = NotificationCreate(
                    user_id=user_id,
                    type=NotificationType.PROJECT_ASSIGNED,
                    title=f"你被指派为项目「{project.name}」的负责人",
                    content=f"你被指派为项目「{project.name}」的负责人",
                    related_id=project.id,
                    related_type="project"
                )
            await NotificationService.create_notification(session, notification)

    @staticmethod
    async def create_team_project_assigned_notifications(
        session: AsyncSession,
        team_member_ids: List[int],
        project: Project
    ):
        """创建团队项目分配通知"""
        for user_id in team_member_ids:
            notification = NotificationCreate(
                user_id=user_id,
                type=NotificationType.PROJECT_ASSIGNED,
                title=f"你的团队被分配了新项目",
                content=f"你的团队被分配了项目「{project.name}」",
                related_id=project.id,
                related_type="project"
            )
            await NotificationService.create_notification(session, notification)