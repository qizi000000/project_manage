<template>


  <!-- 修改状态对话框 -->
  <q-dialog v-model="showStatusDialog">
    <q-card style="min-width: 300px">
      <q-card-section>
        <div class="text-h6">修改项目状态</div>
      </q-card-section>
      <q-card-section class="q-pt-none">
        <q-select
          v-model="editingStatus"
          :options="statusOptions"
          label="项目状态"
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
    <div class="col-12 col-lg-8">
      <div class="q-pa-md" style="font-size: 1.2rem;" >项目名称： {{ project?.name || "项目详情" }}</div>
      <q-expansion-item icon="description" label="项目描述" expand-separator>
        <q-card>
          <q-card-section>
            <div class="text-body1" v-html="project?.description || '<span class=\'text-grey\'>暂无描述</span>'"></div>
          </q-card-section>
        </q-card>
      </q-expansion-item>

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
            <q-card v-for="(c, index) in comments" :key="c.id" flat bordered class="q-pa-md">
              <div class="absolute" style="top:8px; right:8px; display:flex; gap:4px; align-items:center;">
                <q-btn v-if="canEditComment(c)" flat dense round size="sm" icon="edit" color="primary"
                  @click="startEditComment(c)" />
                <q-btn v-if="canDeleteComment(c)" flat dense round size="sm" icon="delete" color="negative"
                  @click="deleteComment(c)" />
                <q-chip dense color="grey-3" text-color="grey-8">#{{ index + 1 }}</q-chip>
              </div>

              <div class="row items-center q-mb-sm">
                <q-avatar color="primary" text-color="white" size="32px">{{ (c.user_nickname || c.user_username ||
                  '?')[0] }}</q-avatar>
                <div class="q-ml-sm">
                  <div class="text-body2 text-weight-medium">{{ c.user_nickname || c.user_username }}</div>
                  <div class="text-caption text-grey-7">{{ formatDate(c.created_at) }}</div>
                </div>
              </div>

              <!-- 编辑模式 -->
              <div v-if="editingCommentId === c.id" class="q-mb-md">
                <q-editor v-model="editCommentContent" :toolbar="editorToolbar" :definitions="editorDefinitions"
                  placeholder="编辑评论内容..." min-height="100px" />
                <div class="row justify-end q-mt-sm q-gutter-sm">
                  <q-btn flat color="grey" label="取消" @click="cancelEditComment" />
                  <q-btn color="primary" label="保存" :loading="updating" @click="updateComment" />
                </div>
              </div>

              <!-- 显示模式 -->
              <div v-else class="text-body2" v-html="formatCommentContent(c.content)"></div>
            </q-card>
          </div>

          <!-- 加载更多按钮 -->
          <div v-if="commentsPagination.hasMore && comments.length > 0" class="q-mt-md text-center">
            <q-btn
              flat
              color="primary"
              :loading="commentsPagination.loading"
              @click="loadMoreComments"
            >
              加载更多评论
            </q-btn>
          </div>

          <div class="q-mt-md">
            <div class="text-caption q-mb-sm">添加评论</div>
            <q-editor v-model="newComment" :toolbar="editorToolbar" :definitions="editorDefinitions"
              placeholder="请输入评论内容..." min-height="120px" />

            <q-dialog v-model="showMentionDialog">
              <q-card style="min-width:300px">
                <q-card-section>
                  <div class="text-h6">选择要@的成员</div>
                </q-card-section>
                <q-card-section class="q-pt-none">
                  <q-list bordered separator>
                    <q-item v-for="m in projectMembersOptions" :key="m.id" clickable v-close-popup
                      @click="addMention(m)">
                      <q-item-section avatar>
                        <q-avatar color="primary" text-color="white">{{ (m.label || '')[0] }}</q-avatar>
                      </q-item-section>
                      <q-item-section>{{ m.label }}</q-item-section>
                    </q-item>
                    <q-item v-if="projectMembersOptions.length === 0"><q-item-section
                        class="text-grey">暂无项目成员</q-item-section></q-item>
                  </q-list>
                </q-card-section>
              </q-card>
            </q-dialog>

            <div class="row justify-end q-mt-sm">
              <q-btn color="primary" label="发布" :loading="posting" @click="postComment" />
            </div>
          </div>
        </q-card-section>
      </q-card>
    </div>

    <div class="col-12 col-lg-4">

      <q-card flat bordered class="q-mb-md">

        <q-card-section class="relative-position">
          <div class="text-subtitle2 q-mb-md">项目信息</div>

          <!-- 项目状态 - 右上角 -->
          <div class="absolute-top-right">
            <q-chip 
              square 
              :color="getStatusColor(project?.status)" 
              text-color="white" 
              :clickable="canEdit"
              @click="canEdit && openStatusDialog()"
            >
              {{ getStatusText(project?.status) || '-' }}
              <q-icon v-if="canEdit" name="edit" size="xs" class="q-ml-xs" />
            </q-chip>
          </div>

          

          <!-- 时间信息 - 开始时间和结束时间在一行 -->
          <div class="q-mb-md">
            <div class="row q-col-gutter-md">
              <div class="col">
                <div class="text-caption text-grey-7 q-mb-xs">开始时间</div>
                <div class="text-body2">{{ project?.start_date ? formatDate(project.start_date) : '-' }}</div>
              </div>
              <div class="col">
                <div class="text-caption text-grey-7 q-mb-xs">结束时间</div>
                <div class="text-body2">{{ project?.end_date ? formatDate(project.end_date) : '-' }}</div>
              </div>
            </div>

            <!-- 进度条 -->
            <div v-if="project?.start_date && project?.end_date" class="q-mt-md">
              <div class="text-caption text-grey-7 q-mb-xs">项目进度</div>
              <q-linear-progress :value="calculateProgress() / 100" :color="getProgressColor()" size="8px"
                class="q-mb-xs" />
              <div class="row justify-between text-caption text-grey-7">
                <span>{{ calculateProgress() }}%</span>
                <span>{{ getDaysRemaining() }}</span>
              </div>
            </div>
          </div>

          <!-- 其他统计信息 -->
          <div class="row q-col-gutter-sm">
            <div class="col-6">
              <q-card flat bordered class="text-center q-pa-sm">
                <div class="text-h6 text-primary">{{ stats.members }}</div>
                <div class="text-caption text-grey-7">成员数</div>
              </q-card>
            </div>
            <div class="col-6">
              <q-card flat bordered class="text-center q-pa-sm">
                <div class="text-h6 text-primary">{{ stats.tasks }}</div>
                <div class="text-caption text-grey-7">任务数</div>
              </q-card>
            </div>
          </div>

          <!-- 项目ID和创建时间 -->
          <div class="row q-mt-md text-caption text-grey-7">
            <div class="col-3">项目ID：{{ project?.id }}</div>
            <div class="col text-right">创建时间：{{ project?.created_at ? formatDate(project.created_at) : '-' }}</div>
          </div>
        </q-card-section>
      </q-card>

      <!-- 项目成员卡片（默认折叠） -->
      <!-- 项目成员卡片（默认折叠） -->
      <q-expansion-item icon="group" label="项目成员" expand-separator :default-opened="false"
        header-class="text-subtitle1">
        <q-card flat bordered>
          <q-card-section class="q-pa-md">
            <div v-if="projectMembers.length === 0" class="text-center text-grey q-pa-lg">
              <q-icon name="people_outline" size="48px" />
              <div class="q-mt-sm">暂无成员</div>
            </div>

            <div v-else class="q-gutter-md">
              <div v-for="member in projectMembersWithStatus" :key="member.id"
                class="row items-center q-pa-sm rounded-borders bg-grey-1"
                style="border-left: 4px solid; border-color: var(--q-primary);">
                <!-- 头像 + 在线状态 -->
                <div class="relative-position">
                  <q-avatar size="48px" class="shadow-2">
                    <q-avatar :color="member.online ? 'primary' : 'grey-5'" text-color="white" size="32px">
                      {{ (member.nickname || member.username || '?')[0] }}
                    </q-avatar>
                  </q-avatar>
                  <!-- 在线状态小圆点 -->
                  <div class="absolute-bottom-right" :class="member.online ? 'bg-positive' : 'bg-grey-5'"
                    style="width:12px; height:12px; border-radius:50%; border:2px solid white;"></div>
                </div>

                <!-- 信息区 -->
                <div class="col q-ml-md">
                  <div class="row items-center q-gutter-xs">
                    <div class="text-body1 text-weight-medium">
                      {{ member.nickname || member.username }}
                    </div>
                    <q-chip :color="member.is_leader ? 'primary' : 'grey-5'" 
                            :text-color="member.is_leader ? 'white' : 'grey-8'" 
                            size="xs" dense>
                      {{ member.is_leader ? '负责人' : '成员' }}
                    </q-chip>
                  </div>
                  <div class="text-caption text-grey-7">
                    角色: {{ member.roles && member.roles.length > 0 ? member.roles.join(', ') : '无' }}
                  </div>
                </div>

                <!-- 操作按钮（可选） -->
                <div class="q-gutter-xs">
                  <q-btn v-if="canEdit.value" round flat dense size="sm" icon="edit" color="grey-7"
                    @click="$router.push(`/projects/${route.params.id}/members`)" />
                </div>
              </div>
            </div>

           
          </q-card-section>
        </q-card>
      </q-expansion-item>

      <!-- 项目附件卡片 -->
      <AttachmentManager
        title="项目附件"
        :api-base-path="`/projects/${route.params.id}`"
        :can-upload="canEdit"
        :can-delete="canEdit"
        class="q-mt-md"
      />
    </div>
  </div>

  <!-- 修改状态对话框 -->
  <q-dialog v-model="showStatusDialog">
    <q-card style="min-width: 300px">
      <q-card-section>
        <div class="text-h6">修改项目状态</div>
      </q-card-section>
      <q-card-section class="q-pt-none">
        <q-select
          v-model="editingStatus"
          :options="statusOptions"
          label="项目状态"
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
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'
import { useUserStore } from 'stores/user'
import AttachmentManager from 'components/AttachmentManager.vue'

const $q = useQuasar()
const route = useRoute()
const userStore = useUserStore()

const project = ref(null)
const stats = ref({ tasks: 0, members: 0, files: 0 })

const canEdit = ref(false)

// 状态修改相关
const showStatusDialog = ref(false)
const editingStatus = ref('')
const updatingStatus = ref(false)

const comments = ref([])
const commentsPagination = ref({
  page: 1,
  page_size: 5,
  total: 0,
  loading: false,
  hasMore: true
})
const newComment = ref('')
const posting = ref(false)
const showMentionDialog = ref(false)
const projectMembers = ref([])
const projectMembersOptions = ref([])

// 计算属性：获取成员的实时在线状态
const projectMembersWithStatus = computed(() => {
  return projectMembers.value.map(member => ({
    ...member,
    online: userStore.getUserOnline(member.id)
  }))
})

// 编辑相关状态
const editingCommentId = ref(null)
const editCommentContent = ref('')
const updating = ref(false)

// 状态选项
const statusOptions = [
  { label: '计划中', value: 'planned' },
  { label: '进行中', value: 'in_progress' },
  { label: '已完成', value: 'completed' },
  { label: '暂停', value: 'on_hold' },
  { label: '取消', value: 'cancelled' },
]

const editorToolbar = [
  ['bold', 'italic', 'strike', 'underline'],
  ['quote', 'unordered', 'ordered'],
  ['link'],
  ['mention'],
  ['undo', 'redo']
]

// 插入@提及的处理器：打开成员选择对话框
const insertMention = () => { showMentionDialog.value = true }

// 编辑器的自定义定义（用于 @ 提及）
const editorDefinitions = {
  mention: {
    tip: '@成员',
    icon: 'alternate_email',
    label: '@',
    handler: insertMention
  }
}


function getStatusColor(status) {
  const colors = { 'planned': 'grey', 'in_progress': 'primary', 'completed': 'positive', 'paused': 'warning', 'cancelled': 'negative' }
  return colors[status] || 'grey'
}

function getStatusText(status) {
  const texts = {
    'planned': '计划中',
    'in_progress': '进行中',
    'completed': '已完成',
    'paused': '暂停',
    'cancelled': '取消'
  }
  return texts[status] || status
}

function calculateProgress() {
  if (!project.value || !project.value.start_date || !project.value.end_date) {
    return 0
  }

  const now = new Date()
  const start = new Date(project.value.start_date)
  const end = new Date(project.value.end_date)

  if (now < start) return 0
  if (now > end) return 100

  const total = end - start
  const elapsed = now - start
  return Math.round((elapsed / total) * 100)
}

function getProgressColor() {
  const progress = calculateProgress()
  if (progress < 30) return 'positive'
  if (progress < 70) return 'warning'
  if (progress < 100) return 'orange'
  return 'negative'
}

function getDaysRemaining() {
  if (!project.value || !project.value.end_date) return null

  const now = new Date()
  const end = new Date(project.value.end_date)
  const diffTime = end - now
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

  if (diffDays < 0) return '已过期'
  if (diffDays === 0) return '今日到期'
  if (diffDays === 1) return '1天'
  return `${diffDays}天`
}



function formatDate(date) {
  if (!date) return '未知'
  return new Date(date).toLocaleString('zh-CN')
}

async function fetchProject() {
  try {
    const { data } = await api.get(`/projects/${route.params.id}`)
    project.value = data
  } catch (err) {
    console.error('获取项目失败', err)
  }
}

async function fetchStats() {
  try {
    const [tasksRes, membersRes, filesRes] = await Promise.all([
      api.get('/tasks/', { params: { project_id: route.params.id, page_size: 1 } }),
      api.get(`/projects/${route.params.id}/members`),
      api.get(`/projects/${route.params.id}/attachments`)
    ])

    stats.value.tasks = tasksRes.data.total || 0
    stats.value.members = membersRes.data.length || 0
    stats.value.files = filesRes.data.length || 0

    projectMembers.value = membersRes.data
    projectMembersOptions.value = membersRes.data.map(m => ({
      id: m.id,
      label: m.nickname || m.username
    }))
    
    // 更新用户在线状态到store
    userStore.updateUsersOnline(membersRes.data)
  } catch (err) {
    console.error('加载失败', err)
  }
}

async function fetchComments(page = 1, append = false) {
  try {
    commentsPagination.value.loading = true
    const { data } = await api.get(`/projects/${route.params.id}/comments`, {
      params: {
        page,
        page_size: commentsPagination.value.page_size
      }
    })

    if (append) {
      comments.value.push(...data.items)
    } else {
      comments.value = data.items
    }

    commentsPagination.value.total = data.total
    commentsPagination.value.page = data.page
    commentsPagination.value.hasMore = data.page * data.page_size < data.total
  } catch (err) {
    console.error('获取评论失败', err)
  } finally {
    commentsPagination.value.loading = false
  }
}

async function postComment() {
  if (!newComment.value.trim()) return
  posting.value = true
  try {
    const mentioned_user_ids = extractMentionedUsers(newComment.value)
    const { data } = await api.post(`/projects/${route.params.id}/comments`, {
      content: newComment.value.trim(),
      mentioned_user_ids
    })
    comments.value.unshift(data)
    newComment.value = ''
  } catch (err) {
    console.error('发布评论失败', err)
    $q.notify({ type: 'negative', message: '发布评论失败' })
  } finally {
    posting.value = false
  }
}

function refreshComments() { fetchComments() }

async function loadMoreComments() {
  const nextPage = commentsPagination.value.page + 1
  await fetchComments(nextPage, true)
}

// 修改项目状态
function openStatusDialog() {
  editingStatus.value = project.value.status
  showStatusDialog.value = true
}

// 更新项目状态
async function updateStatus() {
  updatingStatus.value = true
  try {
    await api.put(`/projects/${route.params.id}`, { status: editingStatus.value })
    project.value.status = editingStatus.value
    $q.notify({ type: 'positive', message: '状态修改成功', position: 'top' })
    showStatusDialog.value = false
  } catch (error) {
    console.error('修改状态失败:', error)
    $q.notify({ 
      type: 'negative', 
      message: error.response?.data?.detail || '修改失败', 
      position: 'top' 
    })
  } finally {
    updatingStatus.value = false
  }
}

function addMention(member) {
  const mentionText = ` @${member.label} `
  if (editingCommentId.value) {
    // 如果正在编辑评论，添加到编辑框
    editCommentContent.value += mentionText
  } else {
    // 否则添加到新评论框
    newComment.value += mentionText
  }
}

function canEditComment(comment) {
  return canEdit.value || comment.user_username === (window.__CURRENT_USER__ && window.__CURRENT_USER__.username)
}

function canDeleteComment(comment) { return canEditComment(comment) }

function startEditComment(comment) {
  editingCommentId.value = comment.id
  // 移除HTML标签，只保留纯文本用于编辑
  editCommentContent.value = comment.content.replace(/<[^>]*>/g, '')
}

function cancelEditComment() {
  editingCommentId.value = null
  editCommentContent.value = ''
}

async function updateComment() {
  if (!editCommentContent.value.trim()) return

  updating.value = true
  try {
    const { data } = await api.put(`/projects/comments/${editingCommentId.value}`, {
      content: editCommentContent.value.trim(),
      mentioned_user_ids: extractMentionedUsers(editCommentContent.value)
    })

    // 更新本地评论列表
    const index = comments.value.findIndex(c => c.id === editingCommentId.value)
    if (index !== -1) {
      comments.value[index] = data
    }

    cancelEditComment()
    $q.notify({ type: 'positive', message: '评论更新成功' })
  } catch (err) {
    console.error('更新评论失败', err)
    $q.notify({ type: 'negative', message: '更新评论失败' })
  } finally {
    updating.value = false
  }
}

async function deleteComment(c) {
  $q.dialog({
    title: '确认删除',
    message: '确定要删除这条评论吗？此操作不可撤销。',
    cancel: {
      label: '取消',
      color: 'primary',
      flat: true
    },
    ok: {
      label: '删除',
      color: 'negative'
    },
    persistent: true
  }).onOk(async () => {
    try {
      await api.delete(`/projects/comments/${c.id}`)
      comments.value = comments.value.filter(x => x.id !== c.id)
      $q.notify({ type: 'positive', message: '评论删除成功' })
    } catch (err) {
      console.error('删除评论失败', err)
      $q.notify({ type: 'negative', message: '删除评论失败' })
    }
  })
}

async function fetchProjectMembers() {
  try {
    const { data } = await api.get(`/projects/${route.params.id}/members`)
    projectMembers.value = data
    projectMembersOptions.value = data.map(m => ({ id: m.id, label: m.nickname || m.username }))
    
    // 更新用户在线状态到store
    userStore.updateUsersOnline(data)
  } catch {
    projectMembers.value = []
    projectMembersOptions.value = []
  }
}

async function checkPermissions() {
  try {
    const { data } = await api.get('/auth/permissions')
    canEdit.value = data.includes('projects.update')
  } catch {
    canEdit.value = false
  }
}

// 从文本内容中提取被@的用户 ID（根据 projectMembersOptions 中的 label 匹配）
function extractMentionedUsers(content) {
  const mentionRegex = /@([^\s@]+)/g
  const ids = []
  if (!content) return ids
  let match
  while ((match = mentionRegex.exec(content)) !== null) {
    const name = match[1]
    const found = projectMembersOptions.value.find(m => m.label === name)
    if (found && !ids.includes(found.id)) ids.push(found.id)
  }
  return ids
}

// 处理评论内容，将@之后的文本显示为蓝色
function formatCommentContent(content) {
  if (!content) return ''
  // 将@用户名替换为蓝色样式的span
  return content.replace(/@([^\s<]+)/g, '<span style="color: #1976d2; font-weight: 500;">@$1</span>')
}

onMounted(async () => {
  await Promise.all([fetchProject(), fetchStats(), fetchComments(), fetchProjectMembers(), checkPermissions()])
})
</script>

<style scoped>
.absolute-top-right {
  position: absolute;
  top: 16px;
  right: 16px;
}
</style>
