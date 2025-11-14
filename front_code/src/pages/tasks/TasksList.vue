<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="text-h6">任务列表</div>
      <q-space />
      <q-btn v-if="canCreate" outline color="primary" label="新建任务" icon="add" @click="openCreate = true" />
    </div>

    <!-- 新建任务弹窗 -->
    <q-dialog v-model="openCreate" persistent :maximized="$q.screen.lt.md">
      <q-card style="max-width: 900px; width: 100%">
        <q-card-section class="row items-center">
          <div class="text-h6">新建任务</div>
          <q-space />
          <q-btn flat round dense icon="close" v-close-popup />
        </q-card-section>
        <q-separator />
        <q-card-section>
          <q-form @submit.prevent="submitTask">
            <div class="row q-col-gutter-md">
              <div class="col-12">
                <q-input v-model="taskForm.title" label="任务标题" outlined dense :rules="[v => !!v || '必填']" />
              </div>
              
              <div class="col-12 col-md-6">
                <q-select 
                  v-model="taskForm.project_id" 
                  :options="projectOptions" 
                  label="所属项目" 
                  outlined 
                  dense 
                  emit-value 
                  map-options 
                  :rules="[v => !!v || '请选择项目']"
                  option-value="id"
                  option-label="name"
                  @update:model-value="onProjectChange"
                />
              </div>
              
              <div class="col-12 col-md-6">
                <q-select 
                  v-model="taskForm.assignee_ids" 
                  :options="projectMemberOptions[taskForm.project_id] || []" 
                  label="负责人" 
                  outlined 
                  dense 
                  multiple 
                  emit-value 
                  map-options 
                  use-chips
                  stack-label
                  option-value="id"
                  option-label="nickname"
                  :disable="!taskForm.project_id"
                  :hint="!taskForm.project_id ? '请先选择项目' : ''"
                />
              </div>
              
              <div class="col-12 col-md-4">
                <q-select v-model="taskForm.status" :options="statusOptions" label="状态" outlined dense emit-value map-options />
              </div>
              
              <div class="col-12 col-md-4">
                <q-select v-model="taskForm.priority" :options="priorityOptions" label="优先级" outlined dense emit-value map-options />
              </div>
              
              <div class="col-12 col-md-4">
                <q-input 
                  v-model="taskForm.estimated_days" 
                  type="number" 
                  label="预计天数" 
                  outlined 
                  dense 
                  min="1"
                  :rules="[v => !v || v > 0 || '预计天数必须大于0']"
                />
              </div>
              
              <div class="col-12">
                <div class="text-caption q-mb-sm">任务描述</div>
                <q-editor 
                  v-model="taskForm.description" 
                  :toolbar="editorToolbar"
                  :definitions="editorDefinitions"
                  placeholder="请输入任务描述..."
                  min-height="120px"
                  max-height="300px"
                />
              </div>
            </div>
            
            <div class="row justify-end q-gutter-sm q-mt-md">
              <q-btn outline color="grey" label="取消" v-close-popup />
              <q-btn outline color="primary" label="创建任务" type="submit" :loading="submitting" />
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

    <q-card flat bordered class="q-mb-md">
      <q-card-section>
        <div class="row q-col-gutter-md items-center">
          <div class="col-12 col-md-3">
            <q-input v-model="filters.title" dense outlined clearable placeholder="搜索任务标题">
              <template #prepend>
                <q-icon name="search" />
              </template>
            </q-input>
          </div>
          <div class="col-6 col-md-2">
            <q-select 
              v-model="filters.project_id" 
              :options="projectOptions" 
              dense 
              outlined 
              label="项目" 
              emit-value 
              map-options 
              clearable 
              option-value="id"
              option-label="name"
            />
          </div>
          <div class="col-6 col-md-2">
            <q-select v-model="filters.status" :options="statusOptions" dense outlined label="状态" emit-value map-options clearable />
          </div>
          <div class="col-6 col-md-2">
            <q-select v-model="filters.priority" :options="priorityOptions" dense outlined label="优先级" emit-value map-options clearable />
          </div>
          <div class="col-6 col-md-2">
            <q-option-group
              v-model="hideCompletedTasks"
              :options="[{ label: '隐藏已完成/取消', value: true }]"
              type="checkbox"
              color="primary"
              dense
            />
          </div>
          <div class="col-6 col-md-1 text-right">
            <q-btn outline color="primary" label="查询" @click="applyFilters" class="q-mr-sm" />
            <q-btn flat color="grey" label="重置" @click="resetFilters" />
          </div>
        </div>
      </q-card-section>
    </q-card>

    <q-table
      :rows="rows"
      :columns="columns"
      row-key="id"
      flat
      bordered
      :loading="loading"
      :pagination="pagination"
      @update:pagination="onPagination"
      :rows-per-page-options="[5, 10, 20, 50]"
    >
      <template #body-cell-priority="props">
        <q-td :props="props">
          <q-chip
            :color="getPriorityColor(props.row.priority)"
            text-color="white"
            dense
            square
            :label="props.row.priority"
          />
        </q-td>
      </template>

      <template #body-cell-status="props">
        <q-td :props="props">
          <q-chip
            :color="getStatusColor(props.row.status)"
            text-color="white"
            dense
            square
            :clickable="canUpdate"
            @click="canUpdate && editTaskStatus(props.row)"
            :label="props.row.status"
          >
            <q-icon v-if="canUpdate" name="edit" size="xs" class="q-ml-xs" />
          </q-chip>
        </q-td>
      </template>

      <template #body-cell-actions="props">
        <q-td :props="props">
          <q-btn flat dense round color="primary" icon="visibility" size="12px" @click="viewTask(props.row)">
            <q-tooltip>查看</q-tooltip>
          </q-btn>
          <q-btn v-if="canUpdate" flat dense round color="secondary" icon="edit" size="12px" @click="editTask(props.row)">
            <q-tooltip>编辑</q-tooltip>
          </q-btn>
          <q-btn v-if="canDelete" flat dense round color="negative" icon="delete" size="12px" @click="deleteTask(props.row)">
            <q-tooltip>删除</q-tooltip>
          </q-btn>
        </q-td>
      </template>

      <template #body-cell-assignees="props">
        <q-td :props="props">
          <div class="q-gutter-xs">
            <q-chip
              v-for="assignee in props.row.assignees"
              :key="assignee.id"
              :label="assignee.nickname"
              size="sm"
              dense
              color="blue-1"
              text-color="blue-8"
            />
          </div>
        </q-td>
      </template>

      <template #body-cell-estimated_days="props">
        <q-td :props="props">
          <span v-if="props.row.estimated_days">{{ props.row.estimated_days }}天</span>
          <span v-else class="text-grey-5">-</span>
        </q-td>
      </template>

      <template #no-data>
        <div class="q-pa-lg text-grey">暂无数据</div>
      </template>
    </q-table>

    <!-- 任务详情对话框 -->
    <q-dialog v-model="openDetail" maximized>
      <q-card>
        <q-card-section class="row items-center">
          <div class="text-h6">{{ detailTask?.title }}</div>
          <q-space />
          <q-btn flat round dense icon="close" v-close-popup />
        </q-card-section>

        <q-card-section>
          <div class="row q-col-gutter-md">
            <div class="col-12 col-md-6">
              <div class="text-caption text-grey-7">状态</div>
              <q-chip :color="getStatusColor(detailTask?.status)" text-color="white" :label="detailTask?.status" />
            </div>
            <div class="col-12 col-md-6">
              <div class="text-caption text-grey-7">优先级</div>
              <q-chip :color="getPriorityColor(detailTask?.priority)" text-color="white" :label="detailTask?.priority" />
            </div>
            <div class="col-12 col-md-6">
              <div class="text-caption text-grey-7">负责人</div>
              <div class="q-gutter-xs q-mt-xs">
                <q-chip
                  v-for="assignee in detailTask?.assignees"
                  :key="assignee.id"
                  :label="assignee.nickname"
                  size="sm"
                  dense
                  color="blue-1"
                  text-color="blue-8"
                />
                <span v-if="!detailTask?.assignees?.length" class="text-grey-5">未分配</span>
              </div>
            </div>
            <div class="col-12 col-md-6">
              <div class="text-caption text-grey-7">项目</div>
              <div class="text-body2">{{ detailTask?.project_name }}</div>
            </div>
            <div class="col-12 col-md-6">
              <div class="text-caption text-grey-7">预计天数</div>
              <div class="text-body2">{{ detailTask?.estimated_days ? `${detailTask.estimated_days}天` : '未设置' }}</div>
            </div>
            <div class="col-12 col-md-6">
              <div class="text-caption text-grey-7">截止时间</div>
              <div class="text-body2">{{ detailTask?.due_date ? formatDate(detailTask.due_date) : '无' }}</div>
            </div>
            <div class="col-12 col-md-6">
              <div class="text-caption text-grey-7">创建者</div>
              <div class="text-body2">{{ detailTask?.created_by_name }}</div>
            </div>
            <div class="col-12">
              <div class="text-caption text-grey-7">描述</div>
              <div class="text-body2 q-mt-sm" v-html="detailTask?.description || '无描述'"></div>
            </div>
          </div>
        </q-card-section>

        <!-- 任务附件 -->
        <AttachmentManager
          :api-base-path="`/tasks/${detailTask?.id}`"
          :can-upload="true"
          :can-delete="true"
          title="任务附件"
        />
      </q-card>
    </q-dialog>

    <!-- 编辑任务对话框 -->
    <q-dialog v-model="openEdit" persistent :maximized="$q.screen.lt.md">
      <q-card style="max-width: 700px; width: 100%">
        <q-card-section class="row items-center">
          <div class="text-h6">编辑任务</div>
          <q-space />
          <q-btn flat round dense icon="close" v-close-popup />
        </q-card-section>
        <q-separator />
        <q-card-section>
          <q-form @submit.prevent="submitEditTask">
            <div class="row q-col-gutter-md">
              <div class="col-12">
                <q-input v-model="editForm.title" label="任务标题" outlined dense :rules="[v => !!v || '必填']" />
              </div>
              
              <div class="col-12 col-md-6">
                <q-select 
                  v-model="editForm.project_id" 
                  :options="projectOptions" 
                  label="所属项目" 
                  outlined 
                  dense 
                  emit-value 
                  map-options 
                  :rules="[v => !!v || '请选择项目']"
                  option-value="id"
                  option-label="name"
                  @update:model-value="onEditProjectChange"
                />
              </div>
              
              <div class="col-12 col-md-6">
                <q-select 
                  v-model="editForm.assignee_ids" 
                  :options="projectMemberOptions[editForm.project_id] || []" 
                  label="负责人" 
                  outlined 
                  dense 
                  multiple 
                  emit-value 
                  map-options 
                  use-chips
                  stack-label
                  option-value="id"
                  option-label="nickname"
                  :disable="!editForm.project_id"
                  :hint="editForm.project_id ? '选择项目成员作为负责人' : '请先选择项目'"
                />
              </div>
              
              <div class="col-12 col-md-4">
                <q-select v-model="editForm.status" :options="statusOptions" label="状态" outlined dense emit-value map-options />
              </div>
              
              <div class="col-12 col-md-4">
                <q-select v-model="editForm.priority" :options="priorityOptions" label="优先级" outlined dense emit-value map-options />
              </div>
              
              <div class="col-12 col-md-4">
                <q-input 
                  v-model="editForm.estimated_days" 
                  type="number" 
                  label="预计天数" 
                  outlined 
                  dense 
                  min="1"
                  :rules="[v => !v || v > 0 || '预计天数必须大于0']"
                />
              </div>
              
              <div class="col-12">
                <div class="text-caption q-mb-sm">任务描述</div>
                <q-editor 
                  v-model="editForm.description" 
                  :toolbar="editorToolbar"
                  :definitions="editorDefinitions"
                  placeholder="请输入任务描述..."
                  min-height="120px"
                  max-height="300px"
                />
              </div>
            </div>
            
            <div class="row justify-end q-gutter-sm q-mt-md">
              <q-btn outline color="red" label="取消" v-close-popup />
              <q-btn outline color="primary" label="保存" type="submit" :loading="submitting" />
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- 修改状态对话框 -->
    <q-dialog v-model="openStatusDialog">
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
          <q-btn flat label="确定" color="primary" @click="updateTaskStatus" :loading="updatingStatus" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'
import AttachmentManager from 'components/AttachmentManager.vue'

const $q = useQuasar()
const router = useRouter()
const route = useRoute()

// 权限控制
const canCreate = ref(true)
const canUpdate = ref(true)
const canDelete = ref(true)

// 数据
const loading = ref(false)
const submitting = ref(false)
const rows = ref([])
const total = ref(0)
const pagination = ref({ page: 1, rowsPerPage: 10 })

// 对话框状态
const openDetail = ref(false)
const openEdit = ref(false)
const openCreate = ref(false)
const openStatusDialog = ref(false)
const editingId = ref(null)
const detailTask = ref(null)
const editingTask = ref(null)
const editingStatus = ref('')
const updatingStatus = ref(false)

// 项目成员选项（响应式）
const projectMemberOptions = ref({})
const projectOptions = ref([])
const userOptions = ref([])

// 表单
const taskForm = ref({
  title: '',
  description: '',
  status: '待处理',
  priority: '中',
  project_id: null,
  assignee_ids: [],
  estimated_days: null
})

const editForm = ref({
  title: '',
  description: '',
  status: '待处理',
  priority: '中',
  project_id: null,
  assignee_ids: [],
  estimated_days: null
})

// 富文本编辑器配置
const editorToolbar = [
  [
    {
      label: '格式',
      icon: 'format_bold',
      list: 'no-icons',
      options: ['bold', 'italic', 'strike', 'underline']
    },
    {
      label: '字体大小',
      icon: 'format_size',
      fixedLabel: true,
      fixedIcon: true,
      list: 'no-icons',
      options: ['size-1', 'size-2', 'size-3', 'size-4', 'size-5']
    },
    'removeFormat'
  ],
  ['quote', 'unordered', 'ordered', 'outdent', 'indent'],
  ['link', 'picture'],
  ['undo', 'redo'],
  ['viewsource', 'fullscreen']
]

const editorDefinitions = {
  size: {
    1: '10px',
    2: '13px',
    3: '16px',
    4: '18px',
    5: '24px',
    6: '32px',
    7: '48px'
  }
}

// 过滤器
const filters = reactive({
  title: '',
  project_id: null,
  status: null,
  priority: null
})

// 隐藏已完成任务开关
const hideCompletedTasks = ref([true])

// 选项
const statusOptions = [
  { label: '待处理', value: '待处理' },
  { label: '进行中', value: '进行中' },
  { label: '已完成', value: '已完成' },
  { label: '已取消', value: '已取消' }
]

const priorityOptions = [
  { label: '低', value: '低' },
  { label: '中', value: '中' },
  { label: '高', value: '高' },
  { label: '紧急', value: '紧急' }
]

// 表格列
const columns = [
  { name: 'id', label: 'ID', field: 'id', align: 'left', sortable: true, style: 'width: 80px' },
  { name: 'title', label: '标题', field: 'title', align: 'left', sortable: true },
  { name: 'status', label: '状态', field: 'status', align: 'left' },
  { name: 'priority', label: '优先级', field: 'priority', align: 'left' },
  { name: 'assignees', label: '负责人', field: 'assignees', align: 'left' },
  { name: 'project_name', label: '项目', field: 'project_name', align: 'left' },
  { name: 'estimated_days', label: '预计天数', field: 'estimated_days', align: 'left' },
  { name: 'due_date', label: '截止时间', field: 'due_date', align: 'left' },
  { name: 'actions', label: '操作', field: 'actions', align: 'left', style: 'width: 120px' }
]

// 获取任务列表
async function fetchTasks() {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.rowsPerPage,
      ...filters
    }
    
    // 如果开启了隐藏已完成任务，添加排除状态参数
    if (hideCompletedTasks.value.includes(true)) {
      params.exclude_status = '已完成,已取消'
    }
    
    const { data } = await api.get('/tasks/', { params })
    rows.value = data.items
    total.value = data.total
  } catch (error) {
    console.error('获取任务列表失败:', error)
    $q.notify({
      type: 'negative',
      message: '获取任务列表失败',
      position: 'top'
    })
  } finally {
    loading.value = false
  }
}

// 应用过滤器
function applyFilters() {
  pagination.value.page = 1
  fetchTasks()
}

// 重置过滤器
function resetFilters() {
  filters.title = ''
  filters.project_id = null
  filters.status = null
  filters.priority = null
  hideCompletedTasks.value = [true]
  applyFilters()
}

// 分页变化
function onPagination(val) {
  pagination.value = val
  fetchTasks()
}

// 查看任务
function viewTask(task) {
  // console.log('查看任务:', task)
  // console.log('任务ID:', task.id)
  if (!task.id) {
    $q.notify({
      type: 'negative',
      message: '任务ID不存在',
      position: 'top'
    })
    return
  }
  router.push({ name: 'task-detail', params: { id: task.id } })
}

// 编辑任务
function editTask(task) {
  console.log('编辑任务:', task)
  if (!task.id) {
    $q.notify({
      type: 'negative',
      message: '任务ID不存在',
      position: 'top'
    })
    return
  }
  
  // 设置编辑ID
  editingId.value = task.id
  
  // 填充编辑表单
  editForm.value = {
    title: task.title || '',
    description: task.description || '',
    status: task.status || '待处理',
    priority: task.priority || '中',
    project_id: task.project_id || null,
    assignee_ids: task.assignee_ids || [],
    estimated_days: task.estimated_days || null
  }
  
  // 打开编辑对话框
  openEdit.value = true
}

// 编辑任务状态
function editTaskStatus(task) {
  editingTask.value = task
  editingStatus.value = task.status
  openStatusDialog.value = true
}

// 更新任务状态
async function updateTaskStatus() {
  if (!editingTask.value) return

  updatingStatus.value = true
  try {
    await api.patch(`/tasks/${editingTask.value.id}`, { status: editingStatus.value })
    $q.notify({ type: 'positive', message: '状态修改成功', position: 'top' })
    openStatusDialog.value = false
    fetchTasks()
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

// 删除任务
async function deleteTask(task) {
  $q.dialog({
    title: '确认删除',
    message: '确定要删除此任务吗？',
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await api.delete(`/tasks/${task.id}`)
      $q.notify({ type: 'positive', message: '任务删除成功', position: 'top' })
      fetchTasks()
    } catch (error) {
      console.error('删除任务失败:', error)
      $q.notify({
        type: 'negative',
        message: error.response?.data?.detail || '删除任务失败',
        position: 'top'
      })
    }
  })
}

// 获取项目成员
async function fetchProjectMembers(projectId) {
  if (!projectId) {
    return
  }
  
  try {
    // 找到对应的项目，获取team_id和owner_id
    const project = projectOptions.value.find(p => p.id === projectId)
    if (!project) {
      console.warn('项目不存在:', projectId)
      projectMemberOptions.value[projectId] = []
      return
    }
    
    let members = []
    
    // 如果项目有团队，获取团队成员
    if (project.team_id) {
      try {
        const { data } = await api.get(`/teams/${project.team_id}/members`)
        members = data.map(member => ({
          id: member.user_id,
          nickname: member.nickname,
          username: member.username
        })) || []
      } catch (error) {
        console.error('获取团队成员失败:', error)
        members = []
      }
    }
    
    // 如果项目有负责人，确保负责人也在成员列表中
    if (project.owner_id) {
      const ownerExists = members.some(member => member.id === project.owner_id)
      if (!ownerExists) {
        // 从用户列表中找到项目负责人
        const owner = userOptions.value.find(user => user.id === project.owner_id)
        if (owner) {
          members.push({
            id: owner.id,
            nickname: owner.nickname,
            username: owner.username
          })
        }
      }
    }
    
    projectMemberOptions.value[projectId] = members
    console.log(`项目 ${projectId} 的可选负责人:`, members)
    
  } catch (error) {
    console.error('获取项目成员失败:', error)
    projectMemberOptions.value[projectId] = []
  }
}

// 项目选择变化
function onProjectChange(projectId) {
  // 清空已选择的负责人
  taskForm.value.assignee_ids = []
  // 获取项目成员
  fetchProjectMembers(projectId)
}

// 编辑项目选择变化
function onEditProjectChange(projectId) {
  // 清空已选择的负责人
  editForm.value.assignee_ids = []
  // 获取项目成员
  fetchProjectMembers(projectId)
}

// 重置表单
function resetForm() {
  taskForm.value = {
    title: '',
    description: '',
    status: '待处理',
    priority: '中',
    project_id: null,
    assignee_ids: [],
    estimated_days: null
  }
  projectMemberOptions.value = {}
}

// 提交创建任务
async function submitTask() {
  submitting.value = true
  try {
    const payload = {
      ...taskForm.value,
      assignee_ids: taskForm.value.assignee_ids || []
    }

    await api.post('/tasks/', payload)
    $q.notify({ type: 'positive', message: '任务创建成功', position: 'top' })

    openCreate.value = false
    resetForm()
    fetchTasks()
  } catch (error) {
    console.error('创建任务失败:', error)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || '创建任务失败',
      position: 'top'
    })
  } finally {
    submitting.value = false
  }
}

// 提交编辑任务
async function submitEditTask() {
  submitting.value = true
  try {
    const payload = {
      ...editForm.value,
      assignee_ids: editForm.value.assignee_ids || []
    }

    await api.patch(`/tasks/${editingId.value}`, payload)
    $q.notify({ type: 'positive', message: '任务更新成功', position: 'top' })

    openEdit.value = false
    editingId.value = null
    fetchTasks()
  } catch (error) {
    console.error('更新任务失败:', error)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || '更新任务失败',
      position: 'top'
    })
  } finally {
    submitting.value = false
  }
}

// 获取项目列表
async function fetchProjects() {
  // console.log('开始获取项目列表...')
  try {
    const { data } = await api.get('/projects/')
    // console.log('获取到的项目数据:', data)
    // 后端直接返回项目数组
    projectOptions.value = data || []
    // console.log('设置的项目选项:', projectOptions.value)
  } catch (error) {
    console.error('获取项目列表失败:', error)
    console.error('错误详情:', error.response?.data)
  }
}

// 获取用户列表
async function fetchUsers() {
  try {
    const { data } = await api.get('/users/')
    userOptions.value = data.items || []
  } catch (error) {
    console.error('获取用户列表失败:', error)
  }
}

// 工具函数
function getPriorityColor(priority) {
  const colors = {
    '低': 'grey',
    '中': 'blue',
    '高': 'orange',
    '紧急': 'red'
  }
  return colors[priority] || 'grey'
}

function getStatusColor(status) {
  const colors = {
    '待处理': 'grey',
    '进行中': 'blue',
    '已完成': 'green',
    '已取消': 'red'
  }
  return colors[status] || 'grey'
}

function formatDate(val) {
  if (!val) return '—'
  try {
    return new Date(val).toLocaleString()
  } catch {
    return String(val)
  }
}

// 初始化
onMounted(async () => {
  fetchTasks()
  fetchProjects()
  fetchUsers()
  
  try {
    const { data } = await api.get('/auth/permissions')
    canCreate.value = data.includes('tasks.create')
    canUpdate.value = data.includes('tasks.update')
    canDelete.value = data.includes('tasks.delete')
  } catch {
    canCreate.value = true // 后端未启用权限时兜底展示
    canUpdate.value = true
    canDelete.value = true
  }
  
  // 检查URL参数，如果有create=true则打开新建任务弹窗
  if (route.query.create === 'true') {
    openCreate.value = true
  }
})

// 监听隐藏已完成任务开关的变化
watch(hideCompletedTasks, () => {
  fetchTasks()
})
</script>
