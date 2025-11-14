<template>
  <q-btn
    flat
    dense
    round
    icon="notifications"
    :color="hasUnread ? 'negative' : 'grey-7'"
    class="notification-btn"
  >
    <q-badge
      v-if="hasUnread"
      :label="unreadCount"
      color="negative"
      floating
      class="notification-badge"
    />

    <q-menu
      anchor="bottom end"
      self="top end"
      :offset="[0, 8]"
      class="notification-menu"
    >
      <q-list class="notification-list">
        <q-item class="notification-header">
          <q-item-section>
            <div class="text-h6">通知</div>
          </q-item-section>
          <q-item-section side>
            <q-btn
              flat
              dense
              label="全部已读"
              color="primary"
              size="sm"
              @click="markAllAsRead"
              :loading="loading"
            />
          </q-item-section>
        </q-item>

        <q-separator />

        <q-item
          v-if="!notifications.length && !loading"
          class="text-grey-6"
        >
          <q-item-section>暂无通知</q-item-section>
        </q-item>

        <q-item
          v-for="notification in notifications"
          :key="notification.id"
          clickable
          @click="handleNotificationClick(notification)"
          :class="{ 'notification-unread': !notification.is_read }"
        >
          <q-item-section avatar>
            <q-icon
              :name="getNotificationIcon(notification.type)"
              :color="getNotificationColor(notification.type)"
              size="md"
            />
          </q-item-section>

          <q-item-section>
            <q-item-label class="notification-title">
              {{ notification.title }}
            </q-item-label>
            <q-item-label caption class="notification-content">
              {{ notification.content }}
            </q-item-label>
            <q-item-label caption class="notification-time">
              {{ formatTime(notification.created_at) }}
            </q-item-label>
          </q-item-section>

          <q-item-section side>
            <q-btn
              flat
              dense
              round
              icon="close"
              size="sm"
              @click.stop="deleteNotification(notification.id)"
            />
          </q-item-section>
        </q-item>

        <q-separator v-if="notifications.length" />

        <q-item
          v-if="notifications.length >= 10"
          clickable
          @click="$router.push('/notifications')"
        >
          <q-item-section class="text-center text-primary">
            查看全部通知
          </q-item-section>
        </q-item>
      </q-list>
    </q-menu>
  </q-btn>
</template>

<script setup>
import {  onMounted, computed } from 'vue'
import { useQuasar } from 'quasar'
import { useRouter } from 'vue-router'
import { useNotificationStore } from 'stores/notification'

const router = useRouter()
const $q = useQuasar()
const store = useNotificationStore()

const loading = computed(() => store.loading)
const notifications = computed(() => store.notifications.slice(0, 10)) // 只显示前10条
const unreadCount = computed(() => store.unreadCount)
const hasUnread = computed(() => store.hasUnread)

onMounted(async () => {
  try {
    await store.fetchNotifications()
  } catch (error) {
    console.error('加载通知失败:', error)
  }
})

function getNotificationIcon(type) {
  const icons = {
    mention: 'alternate_email',
    task_assigned: 'assignment',
    comment_reply: 'reply',
    project_update: 'update',
    team_invite: 'group_add'
  }
  return icons[type] || 'notifications'
}

function getNotificationColor(type) {
  const colors = {
    mention: 'blue',
    task_assigned: 'orange',
    comment_reply: 'green',
    project_update: 'purple',
    team_invite: 'teal'
  }
  return colors[type] || 'grey'
}

function formatTime(dateString) {
  // 处理UTC时间字符串，确保正确解析
  const date = new Date(dateString + (dateString.includes('Z') ? '' : 'Z'))
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`

  // 一周后显示具体日期时间
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function markAllAsRead() {
  try {
    await store.markAllAsRead()
    $q.notify({
      type: 'positive',
      message: '已标记所有通知为已读'
    })
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: '操作失败' + error.message
    })
  }
}

async function deleteNotification(notificationId) {
  try {
    await store.deleteNotification(notificationId)
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: '删除失败' + error.message
    })
  }
}

function handleNotificationClick(notification) {
  // 标记为已读
  if (!notification.is_read) {
    store.markAsRead(notification.id)
  }

  // 根据通知类型跳转到相应页面
  if (notification.related_type === 'project') {
    router.push(`/projects/${notification.related_id}`)
  } else if (notification.related_type === 'task') {
    router.push(`/tasks/${notification.related_id}`)
  } else if (notification.related_type === 'team') {
    router.push(`/teams/${notification.related_id}`)
  }
}
</script>

<style scoped>
.notification-btn {
  position: relative;
}

.notification-badge {
  top: 8px;
  right: 8px;
}

.notification-menu {
  min-width: 350px;
  max-width: 500px;
}

.notification-list {
  max-height: 400px;
  overflow-y: auto;
}

.notification-header {
  padding: 16px;
}

.notification-unread {
  background-color: rgba(0, 123, 255, 0.1);
}

.notification-title {
  font-weight: 500;
  margin-bottom: 4px;
}

.notification-content {
  line-height: 1.4;
  margin-bottom: 4px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.notification-time {
  font-size: 12px;
  color: #666;
}
</style>