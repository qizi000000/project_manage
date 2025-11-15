const routes = [
  // 独立登录布局
  {
    path: '/login',
    component: () => import('layouts/AuthLayout.vue'),
    meta: { public: true },
    children: [
      { path: '', name: 'login', component: () => import('pages/LoginPage.vue'), meta: { public: true } }
    ]
  },
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      { path: '', name: 'home', component: () => import('pages/IndexPage.vue') },
      // 项目管理
      { path: 'projects', name: 'projects-list', component: () => import('pages/projects/ProjectsList.vue'), meta: { permissions: ['projects.view'] } },
      
      // 甘特图
      { path: 'projects/gantt', name: 'projects-gantt', component: () => import('pages/projects/ProjectGantt.vue'), meta: { permissions: ['projects.view'] } },
      // 里程碑
      { path: 'projects/milestones', name: 'projects-milestones', component: () => import('pages/projects/ProjectMilestones.vue'), meta: { permissions: ['projects.view'] } },
      // 统计分析
      { path: 'projects/analytics', name: 'projects-analytics', component: () => import('pages/projects/ProjectAnalytics.vue'), meta: { permissions: ['projects.view'] } },
      
      {
        path: 'projects/:id',
        component: () => import('pages/projects/ProjectDetail.vue'),
        children: [
          { path: '', redirect: { name: 'project-details' } },
          { path: 'details', name: 'project-details', component: () => import('pages/projects/ProjectDetails.vue'), meta: { permissions: ['projects.view'] } },
          { path: 'gantt', name: 'project-gantt', component: () => import('pages/projects/ProjectGantt.vue'), meta: { permissions: ['projects.view'] } },
          { path: 'milestones', name: 'project-milestones', component: () => import('pages/projects/ProjectMilestones.vue'), meta: { permissions: ['projects.view'] } },
        ],
      },
  // 团队管理
  { path: 'teams', name: 'teams-list', component: () => import('pages/teams/TeamsList.vue'), meta: { permissions: ['teams.view'] } },
  { path: 'teams/members', name: 'teams-members', component: () => import('pages/teams/TeamsMembers.vue'), meta: { permissions: ['teams.view'] } },
  { path: 'teams/roles', name: 'teams-roles', component: () => import('pages/teams/TeamsRoles.vue'), meta: { permissions: ['teams.view'] } },
  { path: 'teams/projects', name: 'teams-projects', component: () => import('pages/teams/TeamsProjects.vue'), meta: { permissions: ['teams.view'] } },
  { path: 'teams/settings', name: 'teams-settings', component: () => import('pages/teams/TeamsSettings.vue'), meta: { permissions: ['teams.view'] } },
  
  // 任务管理
  { path: 'tasks', name: 'tasks-list', component: () => import('pages/tasks/TasksList.vue'), meta: { permissions: ['tasks.view'] } },
  { path: 'tasks/:id', name: 'task-detail', component: () => import('pages/tasks/TaskDetail.vue'), meta: { permissions: ['tasks.view'] } },
  { path: 'tasks/gantt', name: 'task-gantt', component: () => import('pages/tasks/TaskGantt.vue'), meta: { permissions: ['tasks.view'] } },
  { path: 'tasks/analytics', name: 'task-analytics', component: () => import('pages/tasks/TaskAnalytics.vue'), meta: { permissions: ['tasks.view'] } },
  // 用户管理
  { path: 'users', name: 'users-list', component: () => import('pages/users/UsersList.vue'), meta: { permissions: ['users.view'] } },
  { path: 'users/roles', name: 'users-roles', component: () => import('pages/users/UsersPermissions.vue'), meta: { permissions: ['roles.view'] } },
  { path: 'users/permissions', name: 'users-permissions', component: () => import('pages/users/UsersPermissions.vue'), meta: { permissions: ['roles.view'] } },
  // 图表分析
  { path: 'analytics/projects', name: 'analytics-projects', component: () => import('pages/analytics/AnalyticsProjects.vue'), meta: { permissions: ['analytics.view'] } },
  { path: 'analytics/users', name: 'analytics-users', component: () => import('pages/analytics/AnalyticsUsers.vue'), meta: { permissions: ['analytics.view'] } },
  { path: 'analytics/tasks', name: 'analytics-tasks', component: () => import('pages/analytics/AnalyticsTasks.vue'), meta: { permissions: ['analytics.view'] } },
  { path: 'analytics/teams', name: 'analytics-teams', component: () => import('pages/analytics/AnalyticsTeams.vue'), meta: { permissions: ['analytics.view'] } },
  { path: 'analytics/roles', name: 'analytics-roles', component: () => import('pages/analytics/AnalyticsRoles.vue'), meta: { permissions: ['analytics.view'] } },
  // 系统设置
  { path: 'settings/general', name: 'settings-general', component: () => import('pages/settings/SettingsGeneral.vue') },
  { path: 'settings/notifications', name: 'settings-notifications', component: () => import('pages/settings/SettingsNotifications.vue') },
    ],
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
    meta: { public: true },
  },
]

export default routes
