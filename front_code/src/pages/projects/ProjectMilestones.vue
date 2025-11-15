<template>
  <div class="">
    <!-- 头部：标题和新建按钮 -->
    <div class="row justify-between items-center q-mb-md">
      <div class="text-h6">项目里程碑</div>
      <q-btn color="primary" icon="add" label="新建里程碑" @click="openCreateDialog" v-if="canCreate" />
    </div>

    <q-timeline :layout="layout" color="primary" class="milestone-timeline">
      <q-timeline-entry v-for="(m, index) in milestones" :key="m.id" :title="m.title"
        :subtitle="'创建人：' + (m.creator?.nickname || m.creator?.username || '未知') + ' · 创建时间:' + formatDate(m.created_at)  "
        :icon="getStatusIcon(m.status)" :color="getStatusColor(m.status)" :side="index % 2 === 0 ? 'left' : 'right'"
        :caption="formatDate(m.created_at)">
        <q-card v-if="index % 2 === 0" class="timeline-card q-mt-sm" :class="`status-${m.status}`" flat bordered>
          <q-card-section>
            <div v-if="m.description" class="text-body2 q-mb-md" v-html="m.description"></div>
            <div class="row items-center text-caption text-grey-7 q-gutter-md q-mb-md">
              <div v-if="m.due_date" class="row items-center">
                <q-icon name="event" size="16px" class="q-mr-xs text-primary" />
                <span>计划完成: {{ formatDate(m.due_date) }}</span>
              </div>
              <div v-if="m.completed_at" class="row items-center">
                <q-icon name="check_circle" size="16px" class="q-mr-xs text-positive" />
                <span>实际完成: {{ formatDate(m.completed_at) }}</span>
              </div>
            </div>
          </q-card-section>
          <q-card-actions class="q-pa-md q-pt-none">
            <q-btn v-if="canEdit" flat dense color="primary" icon="edit" label="编辑" @click="editMilestone(m)" />
            <q-btn v-if="canEdit" flat dense color="negative" icon="delete" label="删除" @click="deleteMilestone(m)" />
          </q-card-actions>
        </q-card>
        <q-card v-else class="timeline-card q-pa-md q-mt-sm" :class="`status-${m.status}`" flat bordered>
          <q-card-section class="q-pa-none">
            <div v-if="m.description" class="text-body2 q-mb-md" v-html="m.description"></div>
            <div class="row items-center text-caption text-grey-7 q-gutter-md q-mb-md">
              <div v-if="m.due_date" class="row items-center">
                <q-icon name="event" size="16px" class="q-mr-xs text-primary" />
                <span>计划完成: {{ formatDate(m.due_date) }}</span>
              </div>
              <div v-if="m.completed_at" class="row items-center">
                <q-icon name="check_circle" size="16px" class="q-mr-xs text-positive" />
                <span>实际完成: {{ formatDate(m.completed_at) }}</span>
              </div>
            </div>
          </q-card-section>
          <q-card-actions class="q-pa-md q-pt-none">
            <q-btn v-if="canEdit" flat dense color="primary" icon="edit" label="编辑" @click="editMilestone(m)" />
            <q-btn v-if="canEdit" flat dense color="negative" icon="delete" label="删除" @click="deleteMilestone(m)" />
          </q-card-actions>
        </q-card>
      </q-timeline-entry>
    </q-timeline>

    <!-- 新建/编辑对话框 -->
    <q-dialog v-model="openCreate" persistent>
      <q-card style="min-width: 400px">
        <q-card-section class="row items-center">
          <div class="text-h6">{{ isEditing ? '编辑里程碑' : '新建里程碑' }}</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section>
          <q-form @submit="submitMilestone" class="q-gutter-md">
            <q-input v-model="form.title" label="标题" required outlined />
            <q-editor v-model="form.description" label="描述" outlined />
            <q-select v-model="form.status" :options="statusOptions" label="状态" outlined />
            <q-input v-model="form.due_date" label="计划完成日期" type="date" outlined />
            <div class="row q-gutter-sm">
              <q-btn type="submit" :loading="submitting" color="primary" label="保存" />
              <q-btn flat label="取消" v-close-popup />
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'

const $q = useQuasar()
const layout = computed(() => {
  return $q.screen.lt.sm ? 'dense' : ($q.screen.lt.md ? 'comfortable' : 'loose')
})
const route = useRoute()

// 状态
const milestones = ref([])
const loading = ref(false)
const openCreate = ref(false)
const submitting = ref(false)
const canCreate = ref(true)
const canEdit = ref(true)
const isEditing = ref(false)
const editingMilestone = ref(null)

// 状态选项
const statusOptions = [
  { label: '待完成', value: 'pending' },
  { label: '已完成', value: 'completed' },
  { label: '已逾期', value: 'overdue' }
]

// 表单
const form = ref({ title: '', description: '', due_date: null, status: statusOptions[0] })

// 加载
async function loadMilestones() {
  if (!route.params.id) return
  loading.value = true
  try {
    const { data } = await api.get(`/projects/${route.params.id}/milestones`)
    milestones.value = data
  } catch {
    $q.notify({ type: 'negative', message: '加载失败' })
  } finally {
    loading.value = false
  }
}

// 新建
function openCreateDialog() {
  isEditing.value = false
  editingMilestone.value = null
  form.value = { title: '', description: '', due_date: null, status: statusOptions[0] }
  openCreate.value = true
}

// 编辑
function editMilestone(milestone) {
  isEditing.value = true
  editingMilestone.value = milestone
  form.value = {
    title: milestone.title,
    description: milestone.description || '',
    due_date: milestone.due_date ? milestone.due_date.split('T')[0] : null,
    status: statusOptions.find(o => o.value === milestone.status) || statusOptions[0]
  }
  openCreate.value = true
}

// 删除
async function deleteMilestone(milestone) {
  $q.dialog({
    title: '确认删除',
    message: `确定要删除里程碑 "${milestone.title}" 吗？`,
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await api.delete(`/projects/milestones/${milestone.id}`)
      $q.notify({ type: 'positive', message: '删除成功' })
      await loadMilestones()
    } catch {
      $q.notify({ type: 'negative', message: '删除失败' })
    }
  })
}

// 提交
async function submitMilestone() {
  submitting.value = true
  try {
    const data = { ...form.value }
    if (typeof data.status === 'object') {
      data.status = data.status.value
    }
    if (isEditing.value) {
      await api.put(`/projects/milestones/${editingMilestone.value.id}`, data)
      $q.notify({ type: 'positive', message: '编辑成功' })
    } else {
      await api.post(`/projects/${route.params.id}/milestones`, data)
      $q.notify({ type: 'positive', message: '创建成功' })
    }
    openCreate.value = false
    form.value = { title: '', description: '', due_date: null, status: 'pending' }
    await loadMilestones()
  } catch {
    $q.notify({ type: 'negative', message: isEditing.value ? '编辑失败' : '创建失败' })
  } finally {
    submitting.value = false
  }
}

// 工具
function formatDate(d) { return d ? new Date(d).toLocaleDateString('zh-CN') : '未设置' }
function getStatusIcon(s) { return { pending: 'schedule', completed: 'check_circle', overdue: 'warning' }[s] || 'schedule' }
function getStatusColor(s) { return { pending: 'grey', completed: 'positive', overdue: 'negative' }[s] || 'grey' }

onMounted(loadMilestones)
</script>

<style scoped>
.milestone-timeline {
  max-width: 800px;
  margin: 0 auto;
}

.timeline-card {
  transition: all 0.3s ease;
  border-left: 4px solid transparent;
}

.timeline-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.timeline-card.status-pending {
  border-left-color: #1976d2;
  background: linear-gradient(135deg, rgba(25, 118, 210, 0.05) 0%, rgba(25, 118, 210, 0.02) 100%);
}

.timeline-card.status-completed {
  border-left-color: #4caf50;
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.05) 0%, rgba(76, 175, 80, 0.02) 100%);
}

.timeline-card.status-overdue {
  border-left-color: #f44336;
  background: linear-gradient(135deg, rgba(244, 67, 54, 0.05) 0%, rgba(244, 67, 54, 0.02) 100%);
}

.q-timeline-entry {
  margin-bottom: 24px;
}

.q-timeline-entry .q-timeline__dot {
  border: 2px solid currentColor;
}

.q-timeline-entry .q-timeline__content {
  margin-left: 16px;
  margin-right: 16px;
}
</style>
