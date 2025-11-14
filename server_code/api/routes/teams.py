from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from db.session import get_session
from db.models.team import Team, TeamMember
from db.models.user import User
from db.models.role import Role
from db.models.user_role import UserRole
from core.notification_service import NotificationService
from api.deps.auth import require_permissions, get_current_user, get_user_permissions
from schemas.team import TeamCreate

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("/")
async def list_teams(session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user), page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100), q: str | None = None):
    # 检查权限：需要teams.view权限，或者只返回用户所属的团队
    has_full_permission = False

    # 检查是否有teams.view权限
    try:
        user_permissions = await get_user_permissions(current_user, session)
        if "teams.view" in user_permissions:
            has_full_permission = True
    except:
        pass

    filters = []
    if q:
        like = f"%{q}%"
        filters.append(Team.name.like(like))

    # 如果没有完整权限，只显示用户所属的团队
    if not has_full_permission:
        user_team_ids = select(TeamMember.team_id).where(TeamMember.user_id == current_user.id)
        filters.append(Team.id.in_(user_team_ids))

    base = select(Team)
    if filters:
        from sqlalchemy import and_ as _and
        base = base.where(_and(*filters))
    total = (await session.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (await session.execute(base.order_by(Team.id.desc()).offset((page-1)*page_size).limit(page_size))).scalars().all()
    
    # 获取每个团队的成员数和在线成员数
    items = []
    for t in rows:
        # 总成员数
        member_count_stmt = select(func.count()).select_from(TeamMember).where(TeamMember.team_id == t.id)
        member_count = (await session.execute(member_count_stmt)).scalar_one()
        
        # 在线成员数
        online_count_stmt = select(func.count()).select_from(TeamMember).join(User, User.id == TeamMember.user_id).where(
            TeamMember.team_id == t.id,
            User.online == True
        )
        online_count = (await session.execute(online_count_stmt)).scalar_one()
        
        items.append({
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "created_at": t.created_at,
            "member_count": member_count,
            "online_count": online_count,
        })
    
    return {"total": total, "items": items}


@router.get("/{team_id}")
async def get_team(team_id: int, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    """获取单个团队详情"""
    # 检查权限：需要teams.view权限，或者是团队成员
    has_permission = False

    # 检查是否有teams.view权限
    try:
        user_permissions = await get_user_permissions(current_user, session)
        if "teams.view" in user_permissions:
            has_permission = True
    except:
        pass

    # 如果没有teams.view权限，检查是否是团队成员
    if not has_permission:
        stmt = select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == current_user.id)
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            has_permission = True

    if not has_permission:
        raise HTTPException(status_code=403, detail="权限不足")

    q = await session.execute(select(Team).where(Team.id == team_id))
    team = q.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="团队不存在")
    
    # 获取成员数和在线数
    member_count_stmt = select(func.count()).select_from(TeamMember).where(TeamMember.team_id == team_id)
    member_count = (await session.execute(member_count_stmt)).scalar_one()
    
    online_count_stmt = select(func.count()).select_from(TeamMember).join(User, User.id == TeamMember.user_id).where(
        TeamMember.team_id == team_id,
        User.online == True
    )
    online_count = (await session.execute(online_count_stmt)).scalar_one()
    
    return {
        "id": team.id,
        "name": team.name,
        "description": team.description,
        "created_at": team.created_at,
        "member_count": member_count,
        "online_count": online_count,
    }


@router.post("/", dependencies=[Depends(require_permissions("teams.create"))])
async def create_team(payload: TeamCreate, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    name = payload.name.strip()
    description = payload.description
    member_ids = payload.member_ids or []

    if not name:
        raise HTTPException(status_code=400, detail="团队名称必填")

    exist = await session.execute(select(Team).where(Team.name == name))
    if exist.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="团队已存在")

    team = Team(name=name, description=description)
    session.add(team)
    await session.commit()
    await session.refresh(team)

    # 如果提供了成员ID，批量添加成员
    added_members = []
    if member_ids:
        for user_id in member_ids:
            # 检查用户是否存在
            u = await session.get(User, user_id)
            if not u:
                continue  # 跳过不存在的用户

            # 检查是否已在团队中（虽然新创建的团队不会有成员，但为了安全）
            exist = await session.execute(
                select(TeamMember).where(TeamMember.team_id == team.id, TeamMember.user_id == user_id)
            )
            if exist.scalar_one_or_none():
                continue  # 已存在，跳过

            # 添加成员
            tm = TeamMember(team_id=team.id, user_id=user_id)
            session.add(tm)
            added_members.append(u)

        await session.commit()

        # 发送通知给新添加的成员
        if added_members:
            await NotificationService.create_team_member_added_notifications(
                session=session,
                new_member_ids=[member.id for member in added_members],
                adder=current_user,
                team_id=team.id,
                team_name=team.name
            )

    return {"id": team.id, "name": team.name, "description": team.description, "created_at": team.created_at}


@router.get("/{team_id}/members")
async def list_members(team_id: int, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    # 检查权限：需要teams.view权限，或者是团队成员
    has_permission = False

    # 检查是否有teams.view权限
    try:
        user_permissions = await get_user_permissions(current_user, session)
        if "teams.view" in user_permissions:
            has_permission = True
    except:
        pass

    # 如果没有teams.view权限，检查是否是团队成员
    if not has_permission:
        stmt = select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == current_user.id)
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            has_permission = True

    if not has_permission:
        raise HTTPException(status_code=403, detail="权限不足")

    t = await session.get(Team, team_id)
    if not t:
        raise HTTPException(status_code=404, detail="团队不存在")
    stmt = select(TeamMember, User, Role).join(User, User.id == TeamMember.user_id).outerjoin(Role, Role.id == User.role_id).where(TeamMember.team_id == team_id)
    res = await session.execute(stmt)
    items = []
    for tm, u, r in res.all():
        # 查询角色名称
        role_names = []
        if u.role_id:
            main_role = await session.execute(select(Role.name).where(Role.id == u.role_id))
            main_role_name = main_role.scalar_one_or_none()
            if main_role_name:
                role_names.append(main_role_name)
        # 查询附加角色
        extra = await session.execute(select(UserRole.role_id).where(UserRole.user_id == u.id))
        extra_role_ids = [r[0] for r in extra.all()]
        if extra_role_ids:
            extra_roles = await session.execute(select(Role.name).where(Role.id.in_(extra_role_ids)))
            role_names.extend([r[0] for r in extra_roles.all() if r[0] and r[0] not in role_names])
        
        items.append({
            "id": tm.id,
            "user_id": u.id,
            "username": u.username,
            "nickname": u.nickname,
            "role_id": u.role_id,
            "roles": role_names,  # 返回角色名称数组
            "is_online": u.online,
            "last_login": u.last_login,
            "created_at": tm.created_at,
        })
    return items


@router.post("/{team_id}/members", dependencies=[Depends(require_permissions("teams.update"))])
async def add_member(team_id: int, payload: dict, session: AsyncSession = Depends(get_session)):
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id 必填")
    t = await session.get(Team, team_id)
    if not t:
        raise HTTPException(status_code=404, detail="团队不存在")
    u = await session.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="用户不存在")
    # 检查是否已存在
    exist = await session.execute(select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id))
    if exist.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="已在团队中")
    tm = TeamMember(team_id=team_id, user_id=user_id)
    session.add(tm)
    await session.commit()
    await session.refresh(tm)
    return {"id": tm.id, "team_id": tm.team_id, "user_id": tm.user_id}


@router.post("/{team_id}/members/batch", dependencies=[Depends(require_permissions("teams.update"))])
async def add_members_batch(team_id: int, payload: dict, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    """批量添加团队成员"""
    user_ids = payload.get("user_ids", [])
    if not user_ids or not isinstance(user_ids, list):
        raise HTTPException(status_code=400, detail="user_ids 必须是数组")
    
    t = await session.get(Team, team_id)
    if not t:
        raise HTTPException(status_code=404, detail="团队不存在")
    
    added = []
    errors = []
    
    for user_id in user_ids:
        # 检查用户是否存在
        u = await session.get(User, user_id)
        if not u:
            errors.append(f"用户ID {user_id} 不存在")
            continue
        
        # 检查是否已在团队中
        exist = await session.execute(
            select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        )
        if exist.scalar_one_or_none():
            errors.append(f"用户 {u.nickname or u.username} 已在团队中")
            continue
        
        # 添加成员
        tm = TeamMember(team_id=team_id, user_id=user_id)
        session.add(tm)
        added.append(user_id)
    
    await session.commit()
    
    # 发送通知给新添加的成员
    if added:
        await NotificationService.create_team_member_added_notifications(
            session=session,
            new_member_ids=added,
            adder=current_user,
            team_id=team_id,
            team_name=t.name
        )
    
    return {
        "added_count": len(added),
        "added_users": added,
        "errors": errors,
    }


@router.delete("/{team_id}/members/{user_id}", dependencies=[Depends(require_permissions("teams.update"))])
async def remove_member(team_id: int, user_id: int, session: AsyncSession = Depends(get_session)):
    t = await session.get(Team, team_id)
    if not t:
        raise HTTPException(status_code=404, detail="团队不存在")
    stmt = delete(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
    await session.execute(stmt)
    await session.commit()
    return {"ok": True}


@router.delete("/{team_id}", dependencies=[Depends(require_permissions("teams.delete"))])
async def delete_team(team_id: int, session: AsyncSession = Depends(get_session)):
    """删除团队"""
    t = await session.get(Team, team_id)
    if not t:
        raise HTTPException(status_code=404, detail="团队不存在")
    
    # 删除团队（会级联删除团队成员）
    await session.delete(t)
    await session.commit()
    return {"ok": True, "message": "团队删除成功"}
