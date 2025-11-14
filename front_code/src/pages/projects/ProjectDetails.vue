<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <q-btn flat round icon="arrow_back" @click="$router.go(-1)" />
      <div class="text-h6 q-ml-sm">{{ project?.name || '项目详情' }}</div>
      <q-space />
      <q-chip square :color="getStatusColor(project?.status)" text-color="white">
        {{ project?.status || '-' }}
      </q-chip>
    </div>

    <div class="row q-col-gutter-md">
      <div class="col-12 col-lg-8">
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
                  <q-btn v-if="canEditComment(c)" flat dense round size="sm" icon="edit" color="primary" @click="startEditComment(c)" />
                  <q-btn v-if="canDeleteComment(c)" flat dense round size="sm" icon="delete" color="negative" @click="deleteComment(c)" />
                  <q-chip dense color="grey-3" text-color="grey-8">#{{ index + 1 }}</q-chip>
                </div>

                <div class="row items-center q-mb-sm">
                  <q-avatar color="primary" text-color="white" size="32px">{{ (c.user_nickname || c.user_username || '?')[0] }}</q-avatar>
                  <div class="q-ml-sm">
                    <div class="text-body2 text-weight-medium">{{ c.user_nickname || c.user_username }}</div>
                    <div class="text-caption text-grey-7">{{ formatDate(c.created_at) }}</div>
                  </div>
                </div>
                <div class="text-body2" v-html="c.content"></div>
              </q-card>
            </div>

            <div class="q-mt-md">
              <div class="text-caption q-mb-sm">添加评论</div>
              <q-editor v-model="newComment" :toolbar="editorToolbar" :definitions="editorDefinitions" placeholder="请输入评论内容..." min-height="120px" />

              <q-dialog v-model="showMentionDialog">
                <q-card style="min-width:300px">
                  <q-card-section>
                    <div class="text-h6">选择要@的成员</div>
                  </q-card-section>
                  <q-card-section class="q-pt-none">
                    <q-list bordered separator>
                      <q-item v-for="m in projectMembersOptions" :key="m.id" clickable v-close-popup @click="addMention(m)">
                        <q-item-section avatar>
                          <q-avatar color="primary" text-color="white">{{ (m.label||'')[0] }}</q-avatar>
                        </q-item-section>
                        <q-item-section>{{ m.label }}</q-item-section>
                      </q-item>
                      <q-item v-if="projectMembersOptions.length === 0"><q-item-section class="text-grey">暂无项目成员</q-item-section></q-item>
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
          <q-card-section>
            <div class="text-subtitle2 q-mb-sm">项目信息</div>
            <div class="row q-col-gutter-md">
              <div class="col-12">项目ID：{{ project?.id }}</div>
              <div class="col-12">成员数：{{ stats.members }}</div>
              <div class="col-12">任务数：{{ stats.tasks }}</div>
              <div class="col-12">创建者：{{ project?.created_by_name }}</div>
              <div class="col-12">创建时间：{{ project?.created_at ? formatDate(project.created_at) : '-' }}</div>
            </div>
          </q-card-section>
        </q-card>

        <AttachmentManager :api-base-path="`/projects/${route.params.id}`" title="项目附件" :can-upload="canEdit" @attachment-updated="onAttachmentUpdated" />
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'
import AttachmentManager from 'components/AttachmentManager.vue'

const $q = useQuasar()
const route = useRoute()

const project = ref(null)
const stats = ref({ tasks: 0, members: 0, files: 0 })

const canEdit = ref(false)

const comments = ref([])
const newComment = ref('')
const posting = ref(false)
const showMentionDialog = ref(false)
const projectMembersOptions = ref([])

const editorToolbar = [
  ['bold', 'italic', 'strike', 'underline'],
  ['quote', 'unordered', 'ordered'],
  ['link'],
  ['mention'],
  ['undo', 'redo']
]

const insertMention = () => { showMentionDialog.value = true }

const editorDefinitions = {
  mention: {
    tip: '@成员',
    icon: 'alternate_email',
    label: '@',
    handler: insertMention
  }
}

function getStatusColor(status) {
  const colors = { '进行中': 'primary', '已完成': 'positive', '暂停': 'warning', '取消': 'negative' }
  return colors[status] || 'grey'
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
    const tasksRes = await api.get('/tasks/', { params: { project_id: route.params.id, page_size: 1 } })
    stats.value.tasks = tasksRes.data.total || 0
    const membersRes = await api.get(`/projects/${route.params.id}/members`)
    stats.value.members = membersRes.data.length || 0
    const filesRes = await api.get(`/projects/${route.params.id}/attachments`)
    stats.value.files = filesRes.data.length || 0
  } catch (err) {
    console.error('加载统计失败', err)
  }
}

async function fetchComments() {
  try {
    const { data } = await api.get(`/projects/${route.params.id}/comments`)
    comments.value = data
  } catch (err) {
    console.error('获取评论失败', err)
  }
}

async function postComment() {
  if (!newComment.value.trim()) return
  posting.value = true
  try {
    const { data } = await api.post(`/projects/${route.params.id}/comments`, { content: newComment.value.trim() })
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

function addMention(member) { newComment.value += ` @${member.label} ` }

function canEditComment(comment) {
  return canEdit.value || comment.user_username === (window.__CURRENT_USER__ && window.__CURRENT_USER__.username)
}

function canDeleteComment(comment) { return canEditComment(comment) }

async function deleteComment(c) {
  try {
    await api.delete(`/projects/${route.params.id}/comments/${c.id}`)
    comments.value = comments.value.filter(x => x.id !== c.id)
  } catch (err) {
    console.error('删除评论失败', err)
  }
}

async function fetchProjectMembers() {
  try {
    const { data } = await api.get(`/projects/${route.params.id}/members`)
    projectMembersOptions.value = data.map(m => ({ id: m.id, label: m.nickname || m.username }))
  } catch {
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

function onAttachmentUpdated() { fetchStats() }

onMounted(async () => {
  await Promise.all([fetchProject(), fetchStats(), fetchComments(), fetchProjectMembers(), checkPermissions()])
})
</script>
