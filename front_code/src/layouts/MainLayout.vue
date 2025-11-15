<template>
  <q-layout view="hHh Lpr fFf">
    <q-header elevated class="header-bg shadow-6 header-rounded">
      <q-toolbar>
        <q-toolbar-title class="logo-section">
          <q-avatar>
            <img :src="$q.dark.isActive ? 'https://cdn.quasar.dev/logo-v2/svg/logo-mono-white.svg' : 'https://cdn.quasar.dev/logo-v2/svg/logo-mono-black.svg'" />
          </q-avatar>
          <span class="logo-text q-pa-md">项目管理系统</span>
        </q-toolbar-title>

        <!-- 右侧：主题按钮 + 通知 + 用户信息 -->
        <q-space />
        <q-btn flat round icon="palette" class="theme-btn" @click="showThemeDialog = true">
          <q-tooltip>主题设置</q-tooltip>
        </q-btn>
        <NotificationDropdown />
        <q-separator vertical inset spaced />

        <q-btn flat no-caps class="q-ml-sm user-btn" padding="xs sm">
          <q-avatar size="28px" class="q-mr-sm">
            <img :src="me?.avatar || defaultAvatar" alt="avatar" />
          </q-avatar>
          <span class="text-body2 ellipsis user-text" style="max-width: 140px">{{ me?.username || '未登录' }}</span>
          <q-menu anchor="bottom right" self="top right">
            <q-list style="min-width: 160px">
              <q-item clickable v-ripple @click="goProfile">
                <q-item-section avatar><q-icon name="person" /></q-item-section>
                <q-item-section>个人中心</q-item-section>
              </q-item>
              <q-separator />
              <q-item clickable v-ripple @click="logout">
                <q-item-section avatar><q-icon name="logout" /></q-item-section>
                <q-item-section>退出登录</q-item-section>
              </q-item>
            </q-list>
          </q-menu>
        </q-btn>
      </q-toolbar>
    </q-header>

    <!-- 主题设置对话框组件 -->
    <theme-settings-dialog v-model="showThemeDialog" />

    <!-- 侧边栏菜单组件 -->
    <sidebar-menu v-model="leftDrawerOpen" :menu-items="menus" />

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>
<style scoped>
.header-rounded {
  border-bottom-left-radius: 8px;
  border-bottom-right-radius: 8px;
  overflow: hidden;
  /* 防止子元素溢出破坏圆角 */
}

/* 主题相关的头部背景色 */
.header-bg {
  background: #ffffff !important;
}

.body--dark .header-bg {
  background: #1a1a1a !important;
}

.q-page-container {
  margin-left: 100 !important;
}

/* 顶部菜单按钮主题颜色 */
.menu-btn,
.theme-btn,
.notification-btn,
.user-btn {
  color: var(--q-primary) !important;
}

.menu-btn:hover,
.theme-btn:hover,
.notification-btn:hover,
.user-btn:hover {
  background-color: rgba(var(--q-primary-rgb), 0.1) !important;
}


.user-text {
  color: var(--q-primary) !important;
}

/* 左侧菜单按钮和logo主题颜色 */
.logo-section .logo-text {
  color: #000000 !important;
}

.body--dark .logo-section .logo-text {
  color: #ffffff !important;
}

</style>
<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { api } from 'boot/axios'
import ThemeSettingsDialog from '../components/ThemeSettingsDialog.vue'
import SidebarMenu from '../components/SidebarMenu.vue'
import NotificationDropdown from '../components/NotificationDropdown.vue'

const router = useRouter()
const $q = useQuasar()

// 主题设置对话框
const showThemeDialog = ref(false)

// 切换侧边栏
const leftDrawerOpen = ref(false)

// 加载主题设置 - 移除，因为主题色现在由独立组件管理

// 用户信息
const me = ref(null)
const defaultAvatar = '/icons/favicon-128x128.png'

onMounted(async () => {
  // 拉取当前用户信息（若未登录会 401，被拦截器处理，这里忽略错误）
  try {
    const { data } = await api.get('/auth/me')
    me.value = data
  } catch (e) {
    // 未登录或接口失败时，不影响布局展示
    console.error('获取当前用户信息失败', e)
  }
})

function goProfile() {
  // 这里可跳到你的个人中心路由；暂用系统设置页占位
  router.push('/settings/general')
}

function logout() {
  localStorage.removeItem('token')
  // 可清理 axios 默认头
  delete api.defaults.headers.common?.Authorization
  const redirect = encodeURIComponent(router.currentRoute.value.fullPath)
  router.push({ name: 'login', query: { redirect } })
}

// 菜单数据（可多级嵌套）
const menus = [
  { label: '仪表盘', icon: 'dashboard', path: '/' },
  {
    label: '任务管理',
    icon: 'task',
    permissions: ['tasks.view'],
    children: [
      { label: '任务列表', icon: 'list', path: '/tasks', permissions: ['tasks.view'] },
      { label: '任务甘特图', icon: 'timeline', path: '/tasks/gantt', permissions: ['tasks.view'] },
      { label: '任务统计', icon: 'bar_chart', path: '/tasks/analytics', permissions: ['tasks.view'] },
    ],
  },
  {
    label: '项目管理',
    icon: 'folder',
    permissions: ['projects.view'],
    children: [
      { label: '项目列表', icon: 'list', path: '/projects', permissions: ['projects.view'] },
      { label: '项目甘特图', icon: 'timeline', path: '/projects/gantt', permissions: ['projects.view'] },
      { label: '项目里程碑', icon: 'flag', path: '/projects/milestones', permissions: ['projects.view'] },
    ],
  },
  {
    label: '团队管理',
    icon: 'group',
    permissions: ['teams.view'],
    children: [
      { label: '团队列表', icon: 'list', path: '/teams', permissions: ['teams.view'] },
      { label: '成员', icon: 'people', path: '/teams/members', permissions: ['teams.view'] },
      { label: '关联项目', icon: 'link', path: '/teams/projects', permissions: ['teams.view'] },
      { label: '设置', icon: 'settings', path: '/teams/settings', permissions: ['teams.view'] },
    ],
  },
  {
    label: '用户管理',
    icon: 'manage_accounts',
    permissions: ['users.view', 'roles.view'],
    children: [
      { label: '用户列表', icon: 'list', path: '/users', permissions: ['users.view'] },
      { label: '角色权限', icon: 'admin_panel_settings', path: '/users/roles', permissions: ['roles.view'] },
    ],
  },
  {
    label: '图表分析',
    icon: 'bar_chart',
    permissions: ['analytics.view'],
    children: [
      { label: '项目统计', icon: 'insert_chart', path: '/analytics/projects', permissions: ['analytics.view'] },
      { label: '用户统计', icon: 'pie_chart', path: '/analytics/users', permissions: ['analytics.view'] },
      { label: '任务统计', icon: 'show_chart', path: '/analytics/tasks', permissions: ['analytics.view'] },
      { label: '团队统计', icon: 'stacked_line_chart', path: '/analytics/teams', permissions: ['analytics.view'] },
      { label: '角色统计', icon: 'multiline_chart', path: '/analytics/roles', permissions: ['analytics.view'] },
    ],
  },
  {
    label: '系统设置',
    icon: 'settings',
    children: [
      { label: '常规设置', icon: 'tune', path: '/settings/general' },
      { label: '通知设置', icon: 'notifications', path: '/settings/notifications' },
    ],
  },
]
</script>
