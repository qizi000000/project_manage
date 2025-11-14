"""系统种子数据定义"""

# 基础权限数据
BASE_PERMISSIONS = [
    # 用户权限
    ("users.view", "查看用户", "users"),
    ("users.create", "创建用户", "users"),
    ("users.update", "更新用户", "users"),
    ("users.delete", "删除用户", "users"),

    # 角色权限
    ("roles.view", "查看角色", "roles"),
    ("roles.create", "创建角色", "roles"),
    ("roles.update", "更新角色", "roles"),
    ("roles.delete", "删除角色", "roles"),

    # 项目权限
    ("projects.view", "查看项目", "projects"),
    ("projects.create", "创建项目", "projects"),
    ("projects.update", "更新项目", "projects"),
    ("projects.delete", "删除项目", "projects"),

    # 任务权限
    ("tasks.view", "查看任务", "tasks"),
    ("tasks.create", "创建任务", "tasks"),
    ("tasks.update", "更新任务", "tasks"),
    ("tasks.delete", "删除任务", "tasks"),

    # 团队权限
    ("teams.view", "查看团队", "teams"),
    ("teams.create", "创建团队", "teams"),
    ("teams.update", "更新团队", "teams"),
    ("teams.delete", "删除团队", "teams"),

    # 图表分析权限
    ("analytics.view", "查看图表分析", "analytics"),
    ("analytics.export", "导出图表数据", "analytics"),
    ("analytics.delete", "删除图表数据", "analytics"),
]

# 内置角色名称
BUILTIN_ROLES = [
    "管理员",
    "项目",
    "运营",
    "采购",
    "美工",
    "前端",
    "后端",
    "全栈",
    "销售",
    "人事"
]

# 默认管理员信息
DEFAULT_ADMIN = {
    "username": "admin",
    "nickname": "默认管理",
    "password": "admin123",
    "is_admin": True
}