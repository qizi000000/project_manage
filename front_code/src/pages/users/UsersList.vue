<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="text-h6">用户列表</div>
      <q-chip square color="grey-3" text-color="grey-9" class="q-ml-sm">共 {{ total }} 人</q-chip>
      <q-space />
      <q-btn v-if="canCreate" outline color="primary" label="新建用户" icon="person_add" @click="onCreateUser" />
    </div>

    <q-card flat bordered class="q-mb-md">
      <q-card-section>
        <div class="row q-col-gutter-md items-center">
          <div class="col-12 col-md-5">
            <q-input v-model="filters.q" dense outlined clearable :debounce="300" placeholder="搜索：用户名 / 昵称 / 备注">
              <template #prepend>
                <q-icon name="search" />
              </template>
            </q-input>
          </div>
          <div class="col-6 col-md-3">
            <q-select v-model="filters.role_id" :options="roleOptions" dense outlined label="角色" emit-value map-options
              clearable />
          </div>
          <div class="col-6 col-md-2">
            <q-select v-model="filters.online" :options="onlineOptions" dense outlined label="在线状态" emit-value
              map-options />
          </div>
          <div class="col-12 col-md-2 text-right">
            <q-btn outline color="primary" label="查询" @click="applyFilters" class="q-mr-sm" />
            <q-btn flat color="grey" label="重置" @click="resetFilters" />
          </div>
        </div>
      </q-card-section>
    </q-card>

    <q-table :rows="rows" :columns="columns" row-key="id" flat bordered :loading="loading" :pagination="pagination"
      @update:pagination="onPagination" :rows-per-page-options="[5, 10, 20, 50]" :separator="'cell'" wrap-cells>
      <!-- 用户名列：头像 + 用户名 + 昵称次要信息 -->
      <template #body-cell-username="props">
        <q-td :props="props">
          <div class="row items-center no-wrap">
            <q-avatar size="28px" color="primary" text-color="white" class="q-mr-sm">{{ initials(props.row.username)
              }}</q-avatar>
            <div>
              <div class="text-body2">{{ props.row.username }}</div>
              <div class="text-caption text-grey-7" v-if="props.row.nickname">{{ props.row.nickname }}</div>
            </div>
          </div>
        </q-td>
      </template>

      <!-- 在线列：图标标识 -->
      <template #body-cell-online="props">
        <q-td :props="props">
          <q-icon :name="isOnline(props.row) ? 'lens' : 'radio_button_unchecked'"
            :color="isOnline(props.row) ? 'positive' : 'grey-5'" size="14px" />
        </q-td>
      </template>

      <!-- 最后上线：可读时间 -->
      <template #body-cell-last_login="props">
        <q-td :props="props">{{ formatDate(props.row.last_login) }}</q-td>
      </template>

      <!-- 角色列：Chip 展示（支持多角色） -->
      <template #body-cell-role="props">
        <q-td :props="props">
          <template v-if="allRoleNames(props.row).length">
            <q-chip v-for="name in allRoleNames(props.row)" :key="name" square dense color="indigo-1" text-color="indigo-9" class="q-mr-xs">
              {{ name }}
            </q-chip>
          </template>
          <template v-else>
            -
          </template>
        </q-td>
      </template>

      <!-- 操作列：查看/编辑/启用禁用 -->
      <template #body-cell-actions="props">
        <q-td :props="props">
          <q-btn flat dense round color="primary" icon="visibility" size="12px" @click="viewUser(props.row)" />
          <q-btn v-if="canUpdate" flat dense round color="secondary" icon="edit" size="12px" @click="editUser(props.row)" />
          <q-btn v-if="canUpdate" flat dense round :icon="props.row.is_active ? 'toggle_on' : 'toggle_off'"
            :color="props.row.is_active ? 'positive' : 'negative'" @click="toggleActive(props.row)" />
        </q-td>
      </template>
      <template #no-data>
        <div class="q-pa-lg text-grey">暂无数据</div>
      </template>
    </q-table>

    <!-- 用户详情 -->
    <q-dialog v-model="openDetail">
      <q-card style="max-width:600px;width:100%">
        <q-card-section class="row items-center">
          <div class="text-h6">用户详情</div>
          <q-space />
          <q-btn flat round dense icon="close" v-close-popup />
        </q-card-section>
        <q-separator />
        <q-card-section>
          <div class="row q-col-gutter-md">
            <div class="col-12 col-md-6">
              <div class="text-caption text-grey-7">用户名</div>
              <div class="text-body2">{{ detailRow?.username }}</div>
            </div>
            <div class="col-12 col-md-6">
              <div class="text-caption text-grey-7">昵称</div>
              <div class="text-body2">{{ detailRow?.nickname || '—' }}</div>
            </div>
            <div class="col-12 col-md-6">
              <div class="text-caption text-grey-7">角色</div>
              <div class="q-mt-xs">
                <template v-if="detailRow">
                  <q-chip v-for="name in allRoleNames(detailRow)" :key="name" square dense color="indigo-1" text-color="indigo-9" class="q-mr-xs q-mb-xs">
                    {{ name }}
                  </q-chip>
                </template>
                <span v-else>—</span>
              </div>
            </div>
            <div class="col-6 col-md-3">
              <div class="text-caption text-grey-7">状态</div>
              <div class="text-body2">{{ detailRow?.is_active ? '启用' : '禁用' }}</div>
            </div>
            <div class="col-6 col-md-3">
              <div class="text-caption text-grey-7">在线</div>
              <div class="text-body2">{{ isOnline(detailRow || {}) ? '在线' : '离线' }}</div>
            </div>
            <div class="col-12 col-md-6">
              <div class="text-caption text-grey-7">创建时间</div>
              <div class="text-body2">{{ formatDate(detailRow?.created_at) }}</div>
            </div>
            <div class="col-12 col-md-6">
              <div class="text-caption text-grey-7">最后上线</div>
              <div class="text-body2">{{ formatDate(detailRow?.last_login) }}</div>
            </div>
            <div class="col-12">
              <div class="text-caption text-grey-7">备注</div>
              <div class="text-body2">{{ detailRow?.remark || '—' }}</div>
            </div>
          </div>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- 新建/编辑用户 -->
    <q-dialog v-model="openCreate" persistent :maximized="$q.screen.lt.md">
      <q-card style="max-width: 700px; width: 100%">
        <q-card-section class="row items-center">
          <div class="text-h6">{{ isEdit ? '编辑用户' : '新建用户' }}</div>
          <q-space />
          <q-btn flat round dense icon="close" v-close-popup />
        </q-card-section>
        <q-separator />
        <q-card-section>
          <q-form @submit.prevent="submitCreate">
            <div class="row q-col-gutter-md">
              <div class="col-12 col-md-6">
                <q-input v-model="createForm.username" label="用户名" outlined dense :rules="[v => !!v || '必填']" />
              </div>
              <div class="col-12 col-md-6" v-if="!isEdit">
                <q-input v-model="createForm.password" type="password" label="密码" outlined dense
                  :rules="[v => !!v || '必填']" />
              </div>
              <div class="col-12 col-md-6">
                <q-input v-model="createForm.nickname" label="昵称" outlined dense />
              </div>
              <div class="col-12 col-md-6" v-if="isEdit">
                <q-input v-model="createForm.new_password" type="password" label="新密码（留空则不修改）" outlined dense clearable
                  :rules="[v => !v || v.length >= 6 || '密码至少6位']" />
              </div>
              <div class="col-12 col-md-6" v-if="isEdit">
                <q-input v-model="createForm.confirm_password" type="password" label="确认新密码" outlined dense clearable
                  :rules="[v => !createForm.new_password || v === createForm.new_password || '两次密码不一致']" />
              </div>
              <div class="col-12 col-md-6">
                <q-select v-model="createForm.role_ids" :options="roleOptions" label="角色（可多选，第一项为主角色）" multiple use-chips outlined dense emit-value
                  map-options />
              </div>
              <div class="col-12">
                <q-input v-model="createForm.remark" type="textarea" label="备注" outlined dense autogrow />
              </div>
            </div>
            <div class="row justify-end q-gutter-sm q-mt-md">
              <q-btn outline color="red" label="取消" v-close-popup />
              <q-btn outline color="primary" :label="isEdit ? '保存' : '创建'" type="submit" :loading="creating" />
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'

const loading = ref(false)
const rows = ref([])
const total = ref(0)
const pagination = ref({ page: 1, rowsPerPage: 10 })
const filters = reactive({ q: '', role_id: null, online: null })
const onlineOptions = [
  { label: '全部', value: null },
  { label: '在线', value: true },
  { label: '离线', value: false },
]
const roleOptions = ref([])
const roleNameMap = reactive({})
const $q = useQuasar()

const columns = [
  { name: 'id', label: 'ID', field: 'id', align: 'left', sortable: true, style: 'width: 80px' },
  { name: 'username', label: '用户名', field: 'username', align: 'left', sortable: true },
  { name: 'nickname', label: '昵称', field: 'nickname', align: 'left' },
  { name: 'role', label: '角色', field: 'role_id', align: 'left' },
  { name: 'online', label: '在线', field: 'online', align: 'left', style: 'width: 60px' },

  { name: 'last_login', label: '最后上线', field: 'last_login', align: 'left' },
  { name: 'created_at', label: '创建时间', field: 'created_at', align: 'left' },
  { name: 'actions', label: '操作', field: 'actions', align: 'left', style: 'width: 160px' },
]

async function fetchRoles() {
  try {
    const { data } = await api.get('/roles/')
    roleOptions.value = data.map(r => ({ label: r.name, value: r.id }))
    data.forEach(r => { roleNameMap[r.id] = r.name })
  } catch (e) { /* noop: 角色加载失败时忽略，页面仍可使用 */
    console.error('获取角色列表失败', e)
  }
}

async function fetchRows() {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.rowsPerPage,
      q: filters.q || undefined,
      role_id: filters.role_id || undefined,
      online: filters.online,
    }
    const { data } = await api.get('/users/', { params })
    rows.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function applyFilters() {
  pagination.value.page = 1
  fetchRows()
}

function resetFilters() {
  filters.q = ''
  filters.role_id = null
  filters.online = null
  applyFilters()
}

watch(pagination, fetchRows)

const openCreate = ref(false)
const openDetail = ref(false)
const creating = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const detailRow = ref(null)
const createForm = ref({ username: '', password: '', nickname: '', role_ids: [], remark: '', new_password: '', confirm_password: '' })
const canCreate = ref(true)
const canUpdate = ref(true)
const canDelete = ref(true)

async function submitCreate() {
  creating.value = true
  try {
    const selected = Array.isArray(createForm.value.role_ids) ? createForm.value.role_ids.filter(Boolean) : []
    const principal = selected.length ? selected[0] : null
    if (isEdit.value && editingId.value) {
      const payload = { username: createForm.value.username, nickname: createForm.value.nickname, role_id: principal, role_ids: selected, remark: createForm.value.remark }
      const { data } = await api.patch(`/users/${editingId.value}`, payload)
      // 如果修改了密码，调用修改密码接口
      if (createForm.value.new_password && createForm.value.new_password === createForm.value.confirm_password) {
        await api.put(`/users/${editingId.value}/password`, { new_password: createForm.value.new_password })
        $q.notify({ type: 'positive', message: '密码已更新', icon: 'check_circle', timeout: 2000 })
      }
      // 更新本地行
      const idx = rows.value.findIndex(r => r.id === data.id)
      if (idx >= 0) rows.value[idx] = { ...rows.value[idx], ...data }
    } else {
      const payload = { username: createForm.value.username, password: createForm.value.password, nickname: createForm.value.nickname, role_id: principal, role_ids: selected, remark: createForm.value.remark }
      await api.post('/users/', payload)
    }
    openCreate.value = false
    createForm.value = { username: '', password: '', nickname: '', role_ids: [], remark: '', new_password: '', confirm_password: '' }
    isEdit.value = false
    editingId.value = null
    await fetchRows()
  } finally {
    creating.value = false
  }
}

onMounted(async () => {
  await fetchRoles()
  await fetchRows()
  try {
    const { data } = await api.get('/auth/permissions')
    canCreate.value = data.includes('users.create')
    canUpdate.value = data.includes('users.update')
    canDelete.value = data.includes('users.delete')
  } catch {
    canCreate.value = true // 后端未启用权限时兜底展示
    canUpdate.value = true
    canDelete.value = true
  }
})

function onPagination(val) {
  pagination.value = val
}

function initials(name) {
  if (!name) return '?'
  const s = String(name).trim()
  return s.slice(0, 1).toUpperCase()
}

function viewUser(row) {
  detailRow.value = { ...row }
  openDetail.value = true
}

function editUser(row) {
  isEdit.value = true
  editingId.value = row.id
  createForm.value = {
    username: row.username,
    password: '',
    nickname: row.nickname || '',
  role_ids: allRoleIds(row),
    remark: row.remark || '',
    new_password: '',
    confirm_password: '',
  }
  openCreate.value = true
}

function onCreateUser() {
  openCreate.value = true
  isEdit.value = false
  editingId.value = null
  createForm.value = { username: '', password: '', nickname: '', role_ids: [], remark: '', new_password: '', confirm_password: '' }
}

async function toggleActive(row) {
  const now = !row.is_active
  try {
    await api.patch(`/users/${row.id}/active`, { is_active: now })
    row.is_active = now
    $q.notify({ type: now ? 'positive' : 'warning', message: now ? '已启用' : '已禁用', icon: now ? 'toggle_on' : 'toggle_off', timeout: 1500 })
  } catch {
    $q.notify({ type: 'negative', message: '操作失败', icon: 'error', timeout: 2000 })
  }
}

function isOnline(row) {
  if (typeof row.online === 'boolean') return row.online
  if (!row.last_login) return false
  const last = new Date(row.last_login).getTime()
  return Date.now() - last <= 10 * 60 * 1000
}

function formatDate(val) {
  if (!val) return '—'
  try {
    return new Date(val).toLocaleString()
  } catch {
    return String(val)
  }
}

function allRoleIds(row) {
  if (!row) return []
  const base = []
  if (row.role_id) base.push(row.role_id)
  if (Array.isArray(row.roles)) {
    for (const rid of row.roles) {
      if (rid && !base.includes(rid)) base.push(rid)
    }
  }
  return base
}

function allRoleNames(row) {
  if (!row) return []
  // 后端已返回角色名称数组，直接使用
  return Array.isArray(row.roles) ? row.roles : []
}
</script>
