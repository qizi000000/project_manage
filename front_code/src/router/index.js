import { defineRouter } from '#q-app/wrappers'
import {
  createRouter,
  createMemoryHistory,
  createWebHistory,
  createWebHashHistory,
} from 'vue-router'
import routes from './routes'

/*
 * If not building with SSR mode, you can
 * directly export the Router instantiation;
 *
 * The function below can be async too; either use
 * async/await or return a Promise which resolves
 * with the Router instance.
 */

export default defineRouter(function (/* { store, ssrContext } */) {
  const createHistory = process.env.SERVER
    ? createMemoryHistory
    : process.env.VUE_ROUTER_MODE === 'history'
      ? createWebHistory
      : createWebHashHistory

  const Router = createRouter({
    scrollBehavior: () => ({ left: 0, top: 0 }),
    routes,

    // Leave this as is and make changes in quasar.conf.js instead!
    // quasar.conf.js -> build -> vueRouterMode
    // quasar.conf.js -> build -> publicPath
    history: createHistory(process.env.VUE_ROUTER_BASE),
  })

  // 全局前置守卫：检查登录态和权限
  Router.beforeEach(async (to, _from, next) => {
    const isPublic = to.matched.some(r => r.meta && r.meta.public)
    if (isPublic) return next()

    const token = localStorage.getItem('token')
    if (!token) {
      const redirect = encodeURIComponent(to.fullPath)
      return next({ name: 'login', query: { redirect } })
    }

    // 检查权限
    const requiredPermissions = to.meta?.permissions
    if (requiredPermissions && requiredPermissions.length > 0) {
      try {
        // 动态导入auth store
        const { useAuthStore } = await import('../stores/auth')
        const authStore = useAuthStore()

        // 确保权限已加载
        if (authStore.permissions.length === 0) {
          await authStore.fetchPermissions()
        }

        // 检查是否有任一所需权限
        const hasPermission = requiredPermissions.some(permission =>
          authStore.hasPermission(permission)
        )

        if (!hasPermission) {
          // 没有权限，重定向到首页或显示错误页面
          console.warn('没有权限访问该页面:', to.path, '需要权限:', requiredPermissions)
          return next({ name: 'home' })
        }
      } catch (error) {
        console.error('权限检查失败:', error)
        return next({ name: 'home' })
      }
    }

    next()
  })

  return Router
})
