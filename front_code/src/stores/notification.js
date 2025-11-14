import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from 'boot/axios'

export const useNotificationStore = defineStore('notification', () => {
  // 状态
  const notifications = ref([])
  const unreadCount = ref(0)
  const loading = ref(false)

  // 计算属性
  const hasUnread = computed(() => unreadCount.value > 0)

  // 方法
  async function fetchNotifications(page = 1, pageSize = 20, onlyUnread = false) {
    loading.value = true
    try {
      const response = await api.get('/notifications/', {
        params: { page, page_size: pageSize, only_unread: onlyUnread }
      })
      if (page === 1) {
        notifications.value = response.data.items
      } else {
        notifications.value.push(...response.data.items)
      }
      unreadCount.value = response.data.unread_count
      return response.data
    } catch (error) {
      console.error('获取通知失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function markAsRead(notificationId) {
    try {
      await api.put(`/notifications/${notificationId}/read`)
      const notification = notifications.value.find(n => n.id === notificationId)
      if (notification && !notification.is_read) {
        notification.is_read = true
        unreadCount.value = Math.max(0, unreadCount.value - 1)
      }
    } catch (error) {
      console.error('标记通知已读失败:', error)
      throw error
    }
  }

  async function markAllAsRead() {
    try {
      await api.put('/notifications/read-all')
      notifications.value.forEach(n => {
        n.is_read = true
      })
      unreadCount.value = 0
    } catch (error) {
      console.error('标记所有通知已读失败:', error)
      throw error
    }
  }

  async function deleteNotification(notificationId) {
    try {
      await api.delete(`/notifications/${notificationId}`)
      const index = notifications.value.findIndex(n => n.id === notificationId)
      if (index > -1) {
        const notification = notifications.value[index]
        notifications.value.splice(index, 1)
        if (!notification.is_read) {
          unreadCount.value = Math.max(0, unreadCount.value - 1)
        }
      }
    } catch (error) {
      console.error('删除通知失败:', error)
      throw error
    }
  }

  // 添加新通知（用于实时推送）
  function addNotification(notification) {
    notifications.value.unshift(notification)
    if (!notification.is_read) {
      unreadCount.value += 1
    }
  }

  return {
    // 状态
    notifications,
    unreadCount,
    loading,

    // 计算属性
    hasUnread,

    // 方法
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    addNotification
  }
})