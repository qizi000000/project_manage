<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="text-h6">项目列表</div>
      <q-space />
  <q-btn v-if="canCreate" outline color="primary" label="新建项目" icon="add" @click="openCreate=true" />
    </div>

    <q-table
      :rows="rows"
      :columns="columns"
      row-key="id"
      flat
      bordered
      :loading="loading"
    >
      <template #body-cell-name="props">
        <q-td :props="props">
          <router-link :to="`/projects/${props.row.id}/details`" class="text-primary">{{ props.row.name }}</router-link>
        </q-td>
      </template>
      <template #body-cell-status="props">
        <q-td :props="props">
          <q-chip 
            square 
            :color="getStatusColor(props.row.status)" 
            text-color="white" 
            :clickable="canUpdate"
            @click="canUpdate && editStatus(props.row)"
            size="sm"
          >
            {{ getStatusLabel(props.row.status) }}
            <q-icon v-if="canUpdate" name="edit" size="xs" class="q-ml-xs" />
          </q-chip>
        </q-td>
      </template>
      <template #body-cell-total_tasks="props">
        <q-td :props="props" class="text-center">
          <q-badge :color="props.row.total_tasks > 0 ? 'primary' : 'grey'" :label="props.row.total_tasks" />
        </q-td>
      </template>
      <template #body-cell-incomplete_tasks="props">
        <q-td :props="props" class="text-center">
          <q-badge :color="props.row.incomplete_tasks > 0 ? 'warning' : 'positive'" :label="props.row.incomplete_tasks" />
        </q-td>
      </template>
      <template #body-cell-actions="props">
        <q-td :props="props">
          <q-btn flat dense round color="primary" icon="visibility" size="12px" @click="viewProject(props.row)">
            <q-tooltip>查看</q-tooltip>
          </q-btn>
          <q-btn v-if="canUpdate" flat dense round color="secondary" icon="edit" size="12px" @click="editProject(props.row)">
            <q-tooltip>编辑</q-tooltip>
          </q-btn>
          <q-btn v-if="canDelete" flat dense round color="negative" icon="delete" size="12px" @click="deleteProject(props.row)" :loading="deletingProjectId === props.row.id">
            <q-tooltip>删除</q-tooltip>
          </q-btn>
        </q-td>
      </template>
      <template #no-data>
        <div class="q-pa-lg text-grey">暂无项目</div>
      </template>
    </q-table>

    <q-dialog v-model="openCreate" persistent :maximized="$q.screen.lt.md">
      <q-card style="max-width: 900px; width: 100%">
        <q-card-section class="row items-center">
          <div class="text-h6">新建项目</div>
          <q-space />
          <q-btn flat round dense icon="close" v-close-popup />
        </q-card-section>
        <q-separator />
        <q-card-section>
          <q-form @submit.prevent="submit">
            <div class="row q-col-gutter-md">
              <div class="col-12 col-md-6">
                <q-input v-model="form.name" label="项目名称 *" outlined dense :rules="[v=>!!v||'请输入项目名称']" />
              </div>
              <div class="col-12 col-md-6">
                <q-select v-model="form.status" :options="statusOptions" label="项目状态 *" outlined dense emit-value map-options />
              </div>
              
              <!-- 项目负责人 -->
              <div class="col-12 col-md-6">
                <q-select
                  :key="leaderSelectKey"
                  v-model="form.leader_ids"
                  :options="userOptions"
                  label="项目负责人（可多选）"
                  outlined
                  dense
                  multiple
                  use-chips
                  emit-value
                  map-options
                  clearable
                  use-input
                  @filter="filterUsers"
                >
                  <template v-slot:no-option>
                    <q-item>
                      <q-item-section class="text-grey">无可用用户</q-item-section>
                    </q-item>
                  </template>
                </q-select>
              </div>
              
              <!-- 所属团队 -->
              <div class="col-12 col-md-6">
                <q-select
                  :key="teamSelectKey"
                  v-model="form.team_id"
                  :options="teamOptions"
                  label="所属团队"
                  outlined
                  dense
                  emit-value
                  map-options
                  option-value="id"
                  option-label="name"
                  clearable
                  use-input
                  @filter="filterTeams"
                >
                  <template v-slot:no-option>
                    <q-item>
                      <q-item-section class="text-grey">无可用团队</q-item-section>
                    </q-item>
                  </template>
                </q-select>
              </div>
              
              <!-- 开发周期 -->
              <div class="col-12 col-md-4">
                <q-input 
                  v-model.number="form.development_days" 
                  type="number" 
                  label="开发周期（天）" 
                  outlined 
                  dense 
                  min="1"
                  hint="自动计算结束日期"
                />
              </div>
              
              <div class="col-6 col-md-4">
                <q-input v-model="form.start_date" type="date" label="开始日期" outlined dense hint="默认今天" />
              </div>
              <div class="col-6 col-md-4">
                <q-input v-model="calculatedEndDate" type="date" label="结束日期" outlined dense readonly hint="自动计算" />
              </div>
              
              <div class="col-12">
                <div class="text-subtitle2 q-mb-xs">项目描述（富文本）</div>
                <q-editor :key="editorKey" v-model="form.description" min-height="180px" />
              </div>
            </div>
            <div class="row justify-end q-gutter-sm q-mt-md">
              <q-btn outline color="red" label="取消" v-close-popup />
              <q-btn outline color="primary" label="创建" type="submit" :loading="submitting" />
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- 修改状态对话框 -->
    <q-dialog v-model="openStatusDialog">
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

    <!-- 编辑项目对话框 -->
    <q-dialog v-model="openEdit" persistent :maximized="$q.screen.lt.md">
      <q-card style="max-width: 900px; width: 100%">
        <q-card-section class="row items-center">
          <div class="text-h6">编辑项目</div>
          <q-space />
          <q-btn flat round dense icon="close" v-close-popup />
        </q-card-section>
        <q-separator />
        <q-card-section>
          <q-form @submit.prevent="updateProject">
            <div class="row q-col-gutter-md">
              <div class="col-12 col-md-6">
                <q-input v-model="editForm.name" label="项目名称 *" outlined dense :rules="[v=>!!v||'请输入项目名称']" />
              </div>
              <div class="col-12 col-md-6">
                <q-select v-model="editForm.status" :options="statusOptions" label="项目状态 *" outlined dense emit-value map-options />
              </div>
              
              <!-- 项目负责人 -->
              <div class="col-12 col-md-6">
                <q-select
                  :key="editLeaderSelectKey"
                  v-model="editForm.leader_ids"
                  :options="userOptions"
                  label="项目负责人（可多选）"
                  outlined
                  dense
                  multiple
                  use-chips
                  emit-value
                  map-options
                  clearable
                  use-input
                  @filter="filterUsers"
                >
                  <template v-slot:no-option>
                    <q-item>
                      <q-item-section class="text-grey">无可用用户</q-item-section>
                    </q-item>
                  </template>
                </q-select>
              </div>
              
              <!-- 所属团队 -->
              <div class="col-12 col-md-6">
                <q-select
                  :key="editTeamSelectKey"
                  v-model="editForm.team_id"
                  :options="teamOptions"
                  label="所属团队"
                  outlined
                  dense
                  emit-value
                  map-options
                  option-value="id"
                  option-label="name"
                  clearable
                  use-input
                  @filter="filterTeams"
                >
                  <template v-slot:no-option>
                    <q-item>
                      <q-item-section class="text-grey">无可用团队</q-item-section>
                    </q-item>
                  </template>
                </q-select>
              </div>
              
              <!-- 开发周期 -->
              <div class="col-12 col-md-4">
                <q-input 
                  v-model.number="editForm.development_days" 
                  type="number" 
                  label="开发周期（天）" 
                  outlined 
                  dense 
                  min="1"
                  hint="自动计算结束日期"
                />
              </div>
              
              <div class="col-6 col-md-4">
                <q-input v-model="editForm.start_date" type="date" label="开始日期" outlined dense hint="默认今天" />
              </div>
              <div class="col-6 col-md-4">
                <q-input v-model="editCalculatedEndDate" type="date" label="结束日期" outlined dense readonly hint="自动计算" />
              </div>
              
              <div class="col-12">
                <div class="text-subtitle2 q-mb-xs">项目描述（富文本）</div>
                <q-editor :key="editEditorKey" v-model="editForm.description" min-height="180px" />
              </div>
            </div>
            <div class="row justify-end q-gutter-sm q-mt-md">
              <q-btn outline color="red" label="取消" v-close-popup />
              <q-btn outline color="primary" label="更新" type="submit" :loading="updating" />
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- 删除确认对话框 -->
    <q-dialog v-model="showDeleteDialog">
      <q-card style="min-width: 350px">
        <q-card-section class="row items-center">
          <q-avatar icon="delete" color="negative" text-color="white" />
          <span class="q-ml-sm">确认删除项目？</span>
        </q-card-section>

        <q-card-section>
          <div class="text-body2">
            您即将删除项目 <strong>"{{ deletingProject?.name }}"</strong>。<br>
            此操作不可撤销，项目的所有相关数据将被永久删除。
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="取消" color="grey" v-close-popup />
          <q-btn 
            flat 
            label="确定删除" 
            color="negative" 
            @click="confirmDelete" 
            :loading="deletingProjectId !== null"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'
import { useRouter, useRoute } from 'vue-router'

const $q = useQuasar()
const router = useRouter()
const route = useRoute()
const loading = ref(false)
const rows = ref([])
const openCreate = ref(false)
const submitting = ref(false)
const editorKey = ref(0)
const editEditorKey = ref(0)
const leaderSelectKey = ref(0)
const editLeaderSelectKey = ref(0)
const teamSelectKey = ref(0)
const editTeamSelectKey = ref(0)
const form = ref({ 
  name: '', 
  description: '', 
  status: 'planned', 
  leader_ids: [],
  team_id: null,
  development_days: 30,
  start_date: new Date().toISOString().split('T')[0],
  end_date: '' 
})
const canCreate = ref(true)
const canUpdate = ref(true)
const canDelete = ref(true)

// 状态修改相关
const openStatusDialog = ref(false)
const editingStatus = ref('')
const updatingStatus = ref(false)
const editingProject = ref(null)

// 编辑项目相关
const openEdit = ref(false)
const updating = ref(false)
const editForm = ref({ 
  name: '', 
  description: '', 
  status: 'planned', 
  leader_ids: [],
  team_id: null,
  development_days: 30,
  start_date: new Date().toISOString().split('T')[0],
  end_date: '' 
})

// 删除项目相关
const deletingProjectId = ref(null)
const showDeleteDialog = ref(false)
const deletingProject = ref(null)

// 编辑项目的计算结束日期
const editCalculatedEndDate = computed(() => {
  if (editForm.value.start_date && editForm.value.development_days > 0) {
    const startDate = new Date(editForm.value.start_date)
    const endDate = new Date(startDate)
    endDate.setDate(startDate.getDate() + editForm.value.development_days)
    return endDate.toISOString().split('T')[0]
  }
  return ''
})

// 用户和团队选项
const userOptions = ref([])
const allUsers = ref([])
const teamOptions = ref([])
const allTeams = ref([])

// 计算结束日期
const calculatedEndDate = computed(() => {
  if (form.value.start_date && form.value.development_days > 0) {
    const startDate = new Date(form.value.start_date)
    const endDate = new Date(startDate)
    endDate.setDate(startDate.getDate() + form.value.development_days)
    return endDate.toISOString().split('T')[0]
  }
  return ''
})

const statusOptions = [
  { label: '计划中', value: 'planned' },
  { label: '进行中', value: 'in_progress' },
  { label: '已完成', value: 'completed' },
  { label: '暂停', value: 'on_hold' },
  { label: '取消', value: 'cancelled' },
]

const columns = [
  { name: 'id', label: 'ID', field: 'id', align: 'left', sortable: true, style: 'width: 80px' },
  { name: 'name', label: '项目名称', field: 'name', align: 'left', sortable: true },
  { name: 'status', label: '状态', field: 'status', align: 'left' },
  { name: 'total_tasks', label: '任务总数', field: 'total_tasks', align: 'center', sortable: true },
  { name: 'incomplete_tasks', label: '未完成任务', field: 'incomplete_tasks', align: 'center', sortable: true },
  { name: 'start_date', label: '开始日期', field: 'start_date', align: 'left' },
  { name: 'end_date', label: '结束日期', field: 'end_date', align: 'left' },
  { name: 'created_at', label: '创建时间', field: 'created_at', align: 'left' },
  { name: 'actions', label: '操作', field: 'actions', align: 'left', style: 'width: 180px' },
]

async function fetchRows() {
  loading.value = true
  try {
    const { data } = await api.get('/projects/')
    rows.value = data
  } catch {
    rows.value = []
  } finally {
    loading.value = false
  }
}

async function submit() {
  submitting.value = true
  try {
    const payload = {
      name: form.value.name,
      description: form.value.description || null,
      status: form.value.status,
      leader_ids: form.value.leader_ids || [],
      team_id: form.value.team_id || null,
      development_days: form.value.development_days || null,
      start_date: form.value.start_date || null,
      end_date: null, // 让后端自动计算
    }
    await api.post('/projects/', payload)
    openCreate.value = false
    // 重置表单
    form.value = { 
      name: '', 
      description: '', 
      status: 'planned', 
      leader_ids: [],
      team_id: null,
      development_days: 30,
      start_date: new Date().toISOString().split('T')[0],
      end_date: '' 
    }
    // 强制重新渲染 q-editor 和 q-select
    editorKey.value++
    leaderSelectKey.value++
    teamSelectKey.value++
    await fetchRows()
    $q.notify({ type: 'positive', message: '项目创建成功', position: 'top' })
  } catch (error) {
    $q.notify({ 
      type: 'negative', 
      message: error.response?.data?.detail || '创建项目失败', 
      position: 'top' 
    })
  } finally {
    submitting.value = false
  }
}

// 查看项目
function viewProject(project) {
  router.push(`/projects/${project.id}/details`)
}

// 修改项目状态
function editStatus(project) {
  editingProject.value = project
  editingStatus.value = project.status
  openStatusDialog.value = true
}

// 更新项目状态
async function updateStatus() {
  if (!editingProject.value) return
  
  updatingStatus.value = true
  try {
    await api.put(`/projects/${editingProject.value.id}`, { status: editingStatus.value })
    $q.notify({ type: 'positive', message: '状态修改成功', position: 'top' })
    openStatusDialog.value = false
    await fetchRows()
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

// 编辑项目
async function editProject(project) {
  try {
    // 获取完整的项目详情（包含描述）
    const { data } = await api.get(`/projects/${project.id}`)
    
    editingProject.value = data
    // 复制项目数据到编辑表单
    editForm.value = {
      name: data.name || '',
      description: data.description || '',
      status: data.status || 'planned',
      leader_ids: data.leader_ids || [],
      team_id: data.team_id || null,
      development_days: data.development_days || 30,
      start_date: data.start_date || new Date().toISOString().split('T')[0],
      end_date: data.end_date || ''
    }
    console.log('编辑项目数据:', data) // 调试信息
    console.log('描述内容:', data.description) // 调试信息
    openEdit.value = true
  } catch (error) {
    console.error('获取项目详情失败:', error)
    $q.notify({
      type: 'negative',
      message: '获取项目详情失败',
      position: 'top'
    })
  }
}

// 更新项目
async function updateProject() {
  if (!editingProject.value) return
  
  updating.value = true
  try {
    const payload = {
      name: editForm.value.name,
      description: editForm.value.description || null,
      status: editForm.value.status,
      leader_ids: editForm.value.leader_ids || [],
      team_id: editForm.value.team_id || null,
      development_days: editForm.value.development_days || null,
      start_date: editForm.value.start_date || null,
      end_date: null, // 让后端自动计算
    }
    
    await api.put(`/projects/${editingProject.value.id}`, payload)
    openEdit.value = false
    // 强制重新渲染编辑表单的 q-editor 和 q-select
    editEditorKey.value++
    editLeaderSelectKey.value++
    editTeamSelectKey.value++
    $q.notify({ type: 'positive', message: '项目更新成功', position: 'top' })
    await fetchRows()
  } catch (error) {
    $q.notify({ 
      type: 'negative', 
      message: error.response?.data?.detail || '更新项目失败', 
      position: 'top' 
    })
  } finally {
    updating.value = false
  }
}

// 删除项目
function deleteProject(project) {
  deletingProject.value = project
  showDeleteDialog.value = true
}

// 确认删除项目
async function confirmDelete() {
  if (!deletingProject.value) return
  
  deletingProjectId.value = deletingProject.value.id
  showDeleteDialog.value = false
  
  try {
    await api.delete(`/projects/${deletingProject.value.id}`)
    $q.notify({ type: 'positive', message: '项目删除成功', position: 'top' })
    await fetchRows()
  } catch (error) {
    console.error('删除项目失败:', error)
    $q.notify({ 
      type: 'negative', 
      message: error.response?.data?.detail || '删除失败', 
      position: 'top' 
    })
  } finally {
    deletingProjectId.value = null
    deletingProject.value = null
  }
}

// 获取状态标签
function getStatusLabel(status) {
  const option = statusOptions.find(opt => opt.value === status)
  return option ? option.label : status
}

// 获取状态颜色
function getStatusColor(status) {
  const colorMap = {
    'planned': 'grey',
    'in_progress': 'primary',
    'completed': 'positive',
    'on_hold': 'warning',
    'cancelled': 'negative'
  }
  return colorMap[status] || 'grey'
}

// 加载用户列表
async function loadUsers() {
  try {
    const response = await api.get('/users/')
    const items = response.data.items || response.data
    allUsers.value = items
    // 转换为 { label, value } 格式，优先显示昵称，否则用户名
    userOptions.value = items.map(u => ({ 
      label: u.nickname || u.username || String(u.id), 
      value: u.id 
    }))
  } catch (error) {
    console.error('加载用户列表失败:', error)
  }
}

// 加载团队列表
async function loadTeams() {
  try {
    const response = await api.get('/teams/')
    allTeams.value = response.data.items || response.data
    teamOptions.value = allTeams.value
  } catch (error) {
    console.error('加载团队列表失败:', error)
  }
}

// 过滤用户
function filterUsers(val, update) {
  update(() => {
    const needle = (val || '').toLowerCase()
    const filtered = needle === ''
      ? allUsers.value
      : allUsers.value.filter(u => (u.nickname || u.username || '').toLowerCase().includes(needle))
    userOptions.value = filtered.map(u => ({ 
      label: u.nickname || u.username || String(u.id), 
      value: u.id 
    }))
  })
}

// 过滤团队
function filterTeams(val, update) {
  update(() => {
    if (val === '') {
      teamOptions.value = allTeams.value
    } else {
      const needle = val.toLowerCase()
      teamOptions.value = allTeams.value.filter(
        (team) => team.name?.toLowerCase().includes(needle)
      )
    }
  })
}

onMounted(async () => {
  await fetchRows()
  await loadUsers()
  await loadTeams()
  
  try {
    const { data } = await api.get('/auth/permissions')
    canCreate.value = data.includes('projects.create')
    canUpdate.value = data.includes('projects.update')
    canDelete.value = data.includes('projects.delete')
  } catch {
    canCreate.value = true // 后端未启用权限时兜底展示
    canUpdate.value = true
    canDelete.value = true
  }

  // 检查URL参数，如果有create=true则打开新建项目弹窗
  if (route.query.create === 'true') {
    openCreate.value = true
  }
})
</script>
