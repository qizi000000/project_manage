import { defineStore } from 'pinia'
import {  reactive } from 'vue'

export const useUserStore = defineStore('user', () => {
  // 用户在线状态映射
  const userOnlineStatus = reactive(new Map())

  // 设置用户在线状态
  function setUserOnline(userId, online) {
    userOnlineStatus.set(userId, online)
  }

  // 获取用户在线状态
  function getUserOnline(userId) {
    return userOnlineStatus.get(userId) || false
  }

  // 更新多个用户的在线状态
  function updateUsersOnline(users) {
    users.forEach(user => {
      if (user.id && user.online !== undefined) {
        setUserOnline(user.id, user.online)
      }
    })
  }

  return {
    userOnlineStatus,
    setUserOnline,
    getUserOnline,
    updateUsersOnline
  }
})