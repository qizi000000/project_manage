import { defineBoot } from '#q-app/wrappers'
import axios from 'axios'
import { Notify } from 'quasar'

// 从环境变量读取 API 地址
const apiBaseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'
const wsURL = import.meta.env.VITE_WS_URL || 'ws://127.0.0.1:8000/ws'

const api = axios.create({ baseURL: apiBaseURL })

let ws = null
let wsTimer = null

function connectWS(router){
  const token = localStorage.getItem('token')
  if (!token) return
  try {
    const url = `${wsURL}?token=${encodeURIComponent(token)}`
    ws = new WebSocket(url)
    ws.onopen = () => {
      // 心跳
      clearInterval(wsTimer)
      wsTimer = setInterval(() => {
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }))
        }
      }, 5000)
    }
    ws.onclose = () => {
      clearInterval(wsTimer)
      wsTimer = null
      ws = null
      // 简单重连，避免登录页反复重连
      const name = router.currentRoute.value.name
      
        setTimeout(() => connectWS(router), 5000)
      
    }
    ws.onerror = () => {
      // 错误由 onclose 统一处理重连
    }
    ws.onmessage = async (ev) => {
      try {
        const msg = JSON.parse(ev.data)
        if (msg.type === 'pong') return
        
        if (msg.type === 'notification') {
          // 处理实时通知
          const { useNotificationStore } = await import('../stores/notification')
          const notificationStore = useNotificationStore()
          notificationStore.addNotification(msg.data)
          
          // 显示通知提示
          Notify.create({
            type: 'info',
            message: msg.data.title,
            caption: msg.data.content.length > 50 ? msg.data.content.substring(0, 50) + '...' : msg.data.content,
            timeout: 5000,
            actions: [{
              label: '查看',
              color: 'primary',
              handler: () => {
                // 根据通知类型跳转到相应页面
                if (msg.data.related_type === 'project') {
                  router.push(`/projects/${msg.data.related_id}`)
                } else if (msg.data.related_type === 'task') {
                  router.push(`/tasks/${msg.data.related_id}`)
                } else if (msg.data.related_type === 'team') {
                  router.push(`/teams/members?teamId=${msg.data.related_id}`)
                }
              }
            }]
          })
        }
      } catch (e) {
        console.error('WebSocket 消息处理失败', e)
      }
    }
  } catch (e) {
    console.error('WebSocket 连接失败', e)
  }
}

function disconnectWS(){
  try {
    if (ws) {
      ws.close()
    }
  } catch (e) {
    console.error('WebSocket 关闭失败', e)
  } finally {
    clearInterval(wsTimer)
    wsTimer = null
    ws = null
  }
}

export default defineBoot(async ({ app, router }) => {
  app.config.globalProperties.$axios = axios
  app.config.globalProperties.$api = api

  // 初始化auth store
  const { useAuthStore } = await import('../stores/auth')
  const authStore = useAuthStore()
  authStore.initializeAuth()

  // 请求拦截：自动附加 Authorization 头
  api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers = config.headers || {}
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  })

  let redirecting = false
  function goLoginWithRedirect() {
    if (redirecting) return
    redirecting = true
    const redirect = encodeURIComponent(router.currentRoute.value.fullPath)
    router.push({ name: 'login', query: { redirect } }).finally(() => {
      setTimeout(() => { redirecting = false }, 300)
    })
  }

  // 响应拦截：401 或网络错误 -> 跳转登录
  api.interceptors.response.use(
    (resp) => resp,
    (error) => {
      const status = error?.response?.status
      const isNetworkError = !error?.response || error?.code === 'ERR_NETWORK'
      if (status === 401 || isNetworkError) {
        // 断开 WS，后端会立即将 online 置为 False
        disconnectWS()
        localStorage.removeItem('token')
        Notify.create({ type: 'warning', message: status === 401 ? '登录已过期，请重新登录' : '无法连接服务器，请重新登录' })
        goLoginWithRedirect()
      }
      return Promise.reject(error)
    }
  )

  // 登录状态变化时尝试连接 WS
  router.afterEach((to) => {
    if (to.name !== 'login') {
      connectWS(router)
    } else {
      // 进入登录页时确保断开连接，立刻标记离线
      disconnectWS()
    }
  })
  // 刷新后仍登录的情况
  connectWS(router)
})

export { api, apiBaseURL }
