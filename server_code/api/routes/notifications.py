"""通知相关路由（中文注释）。"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from typing import List

from db.session import get_session
from db.models.notification import Notification
from schemas.notification import NotificationOut, NotificationListResponse
from api.deps.auth import get_current_user
from db.models.user import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    only_unread: bool = Query(False),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """获取用户通知列表"""
    filters = [Notification.user_id == current_user.id]
    if only_unread:
        filters.append(Notification.is_read == False)

    # 获取总数
    total_stmt = select(func.count()).select_from(
        select(Notification).where(*filters).subquery()
    )
    total = (await session.execute(total_stmt)).scalar_one()

    # 获取未读数量
    unread_stmt = select(func.count()).where(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    )
    unread_count = (await session.execute(unread_stmt)).scalar_one()

    # 获取通知列表
    stmt = select(Notification).where(*filters).order_by(
        Notification.is_read.asc(),  # 未读的排在前面
        Notification.created_at.desc()
    ).offset((page - 1) * page_size).limit(page_size)

    notifications = (await session.execute(stmt)).scalars().all()

    return NotificationListResponse(
        total=total,
        items=[NotificationOut.model_validate(n) for n in notifications],
        unread_count=unread_count
    )


@router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """标记通知为已读"""
    stmt = select(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    )
    notification = (await session.execute(stmt)).scalar_one_or_none()

    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")

    notification.is_read = True
    await session.commit()

    return {"message": "已标记为已读"}


@router.put("/read-all")
async def mark_all_notifications_read(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """标记所有通知为已读"""
    stmt = update(Notification).where(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).values(is_read=True)

    await session.execute(stmt)
    await session.commit()

    return {"message": "已标记所有通知为已读"}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """删除通知"""
    stmt = select(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    )
    notification = (await session.execute(stmt)).scalar_one_or_none()

    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")

    await session.delete(notification)
    await session.commit()

    return {"message": "通知已删除"}