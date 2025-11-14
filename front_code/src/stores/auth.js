import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from 'boot/axios'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const user = ref(null)
  const permissions = ref([])
  const roles = ref([])
  const isAuthenticated = computed(() => !!user.value)

  // 计算属性
  const roleNameMap = computed(() => {
    const map = {}
    roles.value.forEach(role => {
      map[role.id] = role.name
    })
    return map
  })

  // 方法
  async function login(credentials) {
    try {
      const response = await api.post('/auth/login', credentials)
      const { token, user: userData } = response.data

      // 保存token到localStorage
      localStorage.setItem('token', token)

      // 设置axios默认header
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`

      // 设置用户信息
      user.value = userData

      // 获取用户权限
      await fetchPermissions()

      // 获取角色列表（如果有权限）
      if (hasPermission('roles.view')) {
        await fetchRoles()
      }

      return { success: true }
    } catch (error) {
      console.error('登录失败:', error)
      return { success: false, error: error.response?.data?.detail || '登录失败' }
    }
  }

  async function logout() {
    try {
      // 调用登出接口（如果有的话）
      await api.post('/auth/logout')
    } catch (error) {
      console.error('登出接口调用失败:', error)
    }

    // 清理本地状态
    user.value = null
    permissions.value = []

    // 清理token
    localStorage.removeItem('token')
    delete api.defaults.headers.common['Authorization']
  }

  async function fetchUser() {
    try {
      const response = await api.get('/auth/me')
      user.value = response.data
      await fetchPermissions()
      
      // 获取角色列表（如果有权限）
      if (hasPermission('roles.view')) {
        await fetchRoles()
      }
    } catch (error) {
      console.error('获取用户信息失败:', error)
      // 如果获取失败，可能是token过期，清理状态
      await logout()
    }
  }

  async function fetchPermissions() {
    try {
      const response = await api.get('/auth/permissions')
      permissions.value = response.data
    } catch (error) {
      console.error('获取权限失败:', error)
      permissions.value = []
    }
  }

  async function fetchRoles() {
    try {
      const response = await api.get('/roles/')
      roles.value = response.data
    } catch (error) {
      console.error('获取角色列表失败:', error)
      roles.value = []
    }
  }

  function hasPermission(permissionCode) {
    return permissions.value.includes(permissionCode)
  }

  function hasAnyPermission(permissionCodes) {
    return permissionCodes.some(code => hasPermission(code))
  }

  function hasAllPermissions(permissionCodes) {
    return permissionCodes.every(code => hasPermission(code))
  }

  // 初始化：从localStorage恢复token
  function initializeAuth() {
    const token = localStorage.getItem('token')
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`
      // 异步获取用户信息
      fetchUser()
    }
  }

  return {
    // 状态
    user,
    permissions,
    roles,
    isAuthenticated,

    // 计算属性
    roleNameMap,

    // 方法
    login,
    logout,
    fetchUser,
    fetchPermissions,
    fetchRoles,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    initializeAuth
  }
})