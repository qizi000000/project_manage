<template>
  <q-page class="q-pa-md">
    <!-- 顶部：任务标题 + 状态 + 操作按钮 -->
    <div class="row items-center q-mb-md">
      <q-btn flat round icon="arrow_back" @click="$router.go(-1)" />
      <div class="text-h6 q-ml-sm">{{ task?.title || '任务详情' }}</div>
      <q-space />
      <q-chip 
        square 
        :color="getStatusColor(task?.status)" 
        text-color="white" 
        :clickable="canEdit"
        @click="canEdit && openStatusDialog()"
      >
        {{ getStatusText(task?.status) }}
        <q-icon v-if="canEdit" name="edit" size="xs" class="q-ml-xs" />
      </q-chip>
    </div>

    <!-- 修改状态对话框 -->
    <q-dialog v-model="showStatusDialog">
      <q-card style="min-width: 300px">
        <q-card-section>
          <div class="text-h6">修改任务状态</div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-select
            v-model="editingStatus"
            :options="statusOptions"
            label="任务状态"
            outlined
            dense
            emit-value
            map-options
          />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="取消" color="grey" v-close-popup />
          <q-btn flat label="确定" color="primary" @click="updateStatus" :loading="updatingStatus" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <div class="row q-col-gutter-md">
      <!-- 左侧 70% -->
      <div class="col-12 col-lg-8">
        <!-- 任务详情（可折叠） -->
        <q-expansion-item v-model="detailsOpen" icon="description" label="任务详情" expand-separator :dense="$q.screen.lt.md" switch-toggle-side>
          <q-card>
            <q-card-section>
              <div class="row q-col-gutter-md">
                
                <div class="col-12">
                  <div class="text-caption text-grey-7">描述</div>
                  <div class="text-body1" v-html="task?.description || '<span class=\'text-grey\'>暂无描述</span>'"></div>
                </div>
              </div>
            </q-card-section>
          </q-card>
        </q-expansion-item>

        <!-- 评论区：富文本编辑 -->
        <q-card flat bordered class="q-mt-md">
          <q-card-section class="row items-center">
            <div class="text-subtitle1">评论</div>
            <q-space />
            <q-btn flat dense icon="refresh" @click="refreshComments" />
          </q-card-section>
          <q-separator />
          <q-card-section>
            <div v-if="!comments.length" class="text-grey q-pa-sm">暂无评论</div>
            <div v-else class="q-gutter-md">
              <!-- 评论列表 -->
              <q-card v-for="(c, index) in comments" :key="c.id" flat bordered class="q-pa-md">
                <!-- 评论序号和操作按钮 - 右上角 -->
                <div class="absolute" style="top: 8px; right: 8px; display: flex; gap: 4px; align-items: center;">
                  <q-btn
                    v-if="canEditComment(c)"
                    flat
                    dense
                    round
                    size="sm"
                    icon="edit"
                    color="primary"
                    @click="startEditComment(c)"
                  >
                    <q-tooltip>编辑</q-tooltip>
                  </q-btn>
                  <q-btn
                    v-if="canDeleteComment(c)"
                    flat
                    dense
                    round
                    size="sm"
                    icon="delete"
                    color="negative"
                    @click="deleteComment(c)"
                  >
                    <q-tooltip>删除</q-tooltip>
                  </q-btn>
                  <q-chip dense color="grey-3" text-color="grey-8">
                    #{{ (commentPage - 1) * commentPageSize + index + 1 }}
                  </q-chip>
                </div>

                <div class="row items-center q-mb-sm">
                  <q-avatar color="primary" text-color="white" size="32px">
                    {{ c.user?.nickname?.[0] || c.user?.username?.[0] || '?' }}
                  </q-avatar>
                  <div class="q-ml-sm">
                    <div class="text-body2 text-weight-medium">{{ c.user?.nickname || c.user?.username }}</div>
                    <div class="text-caption text-grey-7">{{ formatDate(c.created_at) }}</div>
                  </div>
                </div>
                <div class="text-body2" v-html="c.content"></div>
              </q-card>
            </div>

            <!-- 添加评论 -->
            <div class="q-mt-md">
              <div class="text-caption q-mb-sm">添加评论</div>
              <q-editor
                v-model="newComment"
                :toolbar="editorToolbar"
                :definitions="editorDefinitions"
                placeholder="请输入评论内容..."
                min-height="100px"
                max-height="200px"
              />
              
              <!-- @成员选择弹窗 -->
              <q-dialog v-model="showMentionDialog">
                <q-card style="min-width: 300px">
                  <q-card-section>
                    <div class="text-h6">选择要@的成员</div>
                  </q-card-section>
                  <q-card-section class="q-pt-none">
                    <q-list bordered separator>
                      <q-item 
                        v-for="member in projectMembersOptions" 
                        :key="member.id" 
                        clickable 
                        v-close-popup
                        @click="addMention(member)"
                      >
                        <q-item-section avatar>
                          <q-avatar color="primary" text-color="white">
                            {{ member.label[0] }}
                          </q-avatar>
                        </q-item-section>
                        <q-item-section>{{ member.label }}</q-item-section>
                      </q-item>
                      <q-item v-if="projectMembersOptions.length === 0">
                        <q-item-section class="text-grey">暂无项目成员</q-item-section>
                      </q-item>
                    </q-list>
                  </q-card-section>
                </q-card>
              </q-dialog>
              
              <div class="row justify-end q-mt-sm">
                <q-btn color="primary" label="发布" @click="postComment" :loading="posting" />
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- 右侧 30% -->
      <div class="col-12 col-lg-4">
        <q-card flat bordered class="q-mb-md">
          <q-card-section>
            <div class="row items-center q-mb-sm">
              <div class="text-subtitle2">任务信息</div>
              <q-space />
            </div>
            <div class="row items-center q-col-gutter-md">
              <div class="col-12">
                <q-icon name="folder" class="q-mr-sm" />
                项目：{{ task?.project_name }}
              </div>
              <div class="col-12">
                <q-icon name="flag" class="q-mr-sm" />
                优先级：
                <q-chip
                  :color="getPriorityColor(task?.priority)"
                  text-color="white"
                  dense
                  square
                  size="sm"
                >
                  {{ getPriorityText(task?.priority) }}
                </q-chip>
              </div>
              <div class="col-12">
                <q-icon name="person" class="q-mr-sm" />
                负责人：
                <div class="q-gutter-xs d-inline">
                  <q-chip
                    v-for="assignee in task?.assignees || []"
                    :key="assignee.id"
                    :label="assignee.nickname"
                    size="sm"
                    dense
                    color="blue-1"
                    text-color="blue-8"
                  />
                  <span v-if="!task?.assignees?.length" class="text-grey-5">未分配</span>
                </div>
              </div>
              <div class="col-12" v-if="task?.estimated_days">
                <q-icon name="schedule" class="q-mr-sm" />
                预计天数：{{ task.estimated_days }}天
              </div>
              <div class="col-12" v-if="task?.due_date">
                <q-icon name="event" class="q-mr-sm" />
                截止时间：{{ formatDate(task.due_date) }}
              </div>
              <div class="col-12">
                <q-icon name="create" class="q-mr-sm" />
                创建者：{{ task?.created_by_name }}
              </div>
              <div class="col-12">
                <q-icon name="access_time" class="q-mr-sm" />
                创建时间：{{ task?.created_at ? formatDate(task.created_at) : '-' }}
              </div>
              <div class="col-12" v-if="task?.updated_at">
                <q-icon name="update" class="q-mr-sm" />
                更新时间：{{ formatDate(task.updated_at) }}
              </div>
            </div>
          </q-card-section>
        </q-card>

        <!-- 任务附件 -->
        <AttachmentManager
          :api-base-path="`/tasks/${$route.params.id}`"
          :can-upload="canEdit"
          :can-delete="canEdit"
          title="任务附件"
          @attachment-updated="onAttachmentUpdated"
        />
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'
import AttachmentManager from 'components/AttachmentManager.vue'

const route = useRoute()
const $q = useQuasar()

const task = ref(null)
const canEdit = ref(false)

// 状态修改相关
const showStatusDialog = ref(false)
const editingStatus = ref('')
const updatingStatus = ref(false)

// 评论相关
const comments = ref([])
const newComment = ref('')
const posting = ref(false)
const commentPage = ref(1)
const commentPageSize = ref(20)

// @功能相关
const mentionedUsers = ref([])  // 被@的用户ID列表
const showMentionDialog = ref(false)  // @成员弹窗
const projectMembersOptions = ref([])  // 项目成员选项（用于@功能）

// 详情展开状态
const detailsOpen = ref(true)

// 富文本编辑器配置
const editorToolbar = [
  [
    {
      label: '格式',
      icon: 'format_bold',
      list: 'no-icons',
      options: ['bold', 'italic', 'strike', 'underline']
    }
  ],
  ['quote', 'unordered', 'ordered', 'outdent', 'indent'],
  ['link'],
  ['mention'],
  ['undo', 'redo']
]

const editorDefinitions = {
  mention: {
    tip: '@成员',
    icon: 'alternate_email',
    label: '@',
    handler: insertMention
  },
  size: {
    1: '10px',
    2: '13px',
    3: '16px',
    4: '18px',
    5: '24px'
  }
}

// 状态选项
const statusOptions = [
  { label: '待处理', value: '待处理' },
  { label: '进行中', value: '进行中' },
  { label: '已完成', value: '已完成' },
  { label: '已取消', value: '已取消' }
]

// 获取任务详情
async function fetchTask() {
  
  
  if (!route.params.id) {
    console.error('任务ID参数不存在')
    $q.notify({
      type: 'negative',
      message: '任务ID参数不存在',
      position: 'top'
    })
    return
  }
  
  const taskId = parseInt(route.params.id)
  if (isNaN(taskId)) {
    console.error('任务ID不是有效数字:', route.params.id)
    $q.notify({
      type: 'negative',
      message: '无效的任务ID',
      position: 'top'
    })
    return
  }
  
  try {
    const { data } = await api.get(`/tasks/${taskId}`)
    task.value = data
    // 获取项目成员用于@功能
    if (data.project_id) {
      await fetchProjectMembers(data.project_id)
    }
  } catch (error) {
    console.error('获取任务详情失败:', error)
    $q.notify({
      type: 'negative',
      message: '获取任务详情失败',
      position: 'top'
    })
  }
}

// 获取项目成员（用于@功能）
async function fetchProjectMembers(projectId) {
  try {
    const { data } = await api.get(`/projects/${projectId}/members`)
    projectMembersOptions.value = data.map(member => ({
      id: member.id,
      label: member.nickname || member.username
    }))
  } catch (error) {
    console.error('获取项目成员失败:', error)
    projectMembersOptions.value = []
  }
}

// 检查编辑权限
async function checkPermissions() {
  try {
    const { data } = await api.get('/auth/permissions')
    canEdit.value = data.includes('tasks.update')
  } catch {
    canEdit.value = false
  }
}

// 打开状态修改对话框
function openStatusDialog() {
  editingStatus.value = task.value.status
  showStatusDialog.value = true
}

// 更新任务状态
async function updateStatus() {
  updatingStatus.value = true
  try {
    await api.patch(`/tasks/${route.params.id}`, { status: editingStatus.value })
    task.value.status = editingStatus.value
    showStatusDialog.value = false
    $q.notify({
      type: 'positive',
      message: '任务状态更新成功',
      position: 'top'
    })
  } catch (error) {
    console.error('更新任务状态失败:', error)
    $q.notify({
      type: 'negative',
      message: '更新任务状态失败',
      position: 'top'
    })
  } finally {
    updatingStatus.value = false
  }
}

// 获取评论列表
async function fetchComments() {
  try {
    const { data } = await api.get(`/tasks/${route.params.id}/comments`, {
      params: { page: commentPage.value, page_size: commentPageSize.value }
    })
    comments.value = data.items || []
  } catch (error) {
    console.error('获取评论失败:', error)
  }
}

// 刷新评论
function refreshComments() {
  fetchComments()
}

// 发布评论
async function postComment() {
  if (!newComment.value.trim()) {
    $q.notify({
      type: 'warning',
      message: '请输入评论内容',
      position: 'top'
    })
    return
  }

  posting.value = true
  try {
    await api.post(`/tasks/${route.params.id}/comments`, {
      content: newComment.value,
      mentioned_users: mentionedUsers.value
    })
    newComment.value = ''
    mentionedUsers.value = [] // 清空被@的用户列表
    fetchComments()
    $q.notify({
      type: 'positive',
      message: '评论发布成功',
      position: 'top'
    })
  } catch (error) {
    console.error('发布评论失败:', error)
    $q.notify({
      type: 'negative',
      message: '发布评论失败',
      position: 'top'
    })
  } finally {
    posting.value = false
  }
}

// 打开@成员对话框
function insertMention() {
  showMentionDialog.value = true
}

// 添加@成员
function addMention(member) {
  // 在富文本中插入@成员标签（蓝色显示）
  const mentionTag = `<span style="color: #1976d2; font-weight: 500;">@${member.label}</span>&nbsp;`
  newComment.value += mentionTag
  
  // 添加到被@列表
  if (!mentionedUsers.value.includes(member.id)) {
    mentionedUsers.value.push(member.id)
  }
}

// 删除评论
async function deleteComment(comment) {
  $q.dialog({
    title: '确认删除',
    message: '确定要删除这条评论吗？',
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await api.delete(`/tasks/${route.params.id}/comments/${comment.id}`)
      fetchComments()
      $q.notify({
        type: 'positive',
        message: '评论删除成功',
        position: 'top'
      })
    } catch (error) {
      console.error('删除评论失败:', error)
      $q.notify({
        type: 'negative',
        message: '删除评论失败',
        position: 'top'
      })
    }
  })
}

// 开始编辑评论
function startEditComment() {
  // 这里可以实现编辑评论的功能
  $q.notify({
    type: 'info',
    message: '编辑评论功能待实现',
    position: 'top'
  })
}

// 检查是否可以编辑评论
function canEditComment(comment) {
  // 暂时只允许评论作者编辑
  return comment.user_id === task.value?.created_by
}

// 检查是否可以删除评论
function canDeleteComment(comment) {
  // 允许评论作者或任务创建者删除
  return comment.user_id === task.value?.created_by || canEdit.value
}

// 附件更新事件处理
function onAttachmentUpdated() {
  console.log('任务附件已更新')
}

// 日期格式化
function formatDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 状态相关工具函数
function getStatusColor(status) {
  const colors = {
    '待处理': 'grey',
    '进行中': 'blue',
    '已完成': 'positive',
    '已取消': 'negative'
  }
  return colors[status] || 'grey'
}

function getStatusText(status) {
  return status || '未知'
}

function getPriorityColor(priority) {
  const colors = {
    '低': 'green',
    '中': 'orange',
    '高': 'negative',
    '紧急': 'red'
  }
  return colors[priority] || 'grey'
}

function getPriorityText(priority) {
  return priority || '未知'
}

onMounted(async () => {
  await Promise.all([
    fetchTask(),
    checkPermissions(),
    fetchComments()
  ])
})

// 监听路由参数变化
watch(() => route.params.id, async (newId) => {
  if (newId) {
    await Promise.all([
      fetchTask(),
      fetchComments()
    ])
  }
})
</script>