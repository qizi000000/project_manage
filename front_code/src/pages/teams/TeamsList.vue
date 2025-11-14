<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="text-h6">团队列表</div>
      <q-chip square color="grey-3" text-color="grey-9" class="q-ml-sm">共 {{ total }} 个</q-chip>
      <q-space />
      <q-btn v-if="canCreate" outline color="primary" icon="group_add" label="新建团队" @click="openCreate=true" />
    </div>

    <q-card flat bordered>
      <q-table :rows="rows" :columns="columns" row-key="id" flat :loading="loading">
        <template #body-cell-member_count="props">
          <q-td :props="props">
            <q-chip dense color="blue-2" text-color="blue-8" icon="people">
              {{ props.row.member_count || 0 }}
            </q-chip>
          </q-td>
        </template>
        <template #body-cell-online_count="props">
          <q-td :props="props">
            <q-chip dense color="green-2" text-color="green-8" icon="wifi">
              {{ props.row.online_count || 0 }}
            </q-chip>
          </q-td>
        </template>
        <template #body-cell-actions="props">
          <q-td :props="props">
            <q-btn flat dense color="primary" icon="group" label="成员" @click="goMembers(props.row)" />
            <q-btn v-if="canDelete" flat dense color="negative" icon="delete" label="删除" @click="confirmDelete(props.row)" />
          </q-td>
        </template>
        <template #no-data>
          <div class="q-pa-lg text-grey">暂无团队</div>
        </template>
      </q-table>
    </q-card>

    <q-dialog v-model="openCreate">
      <q-card style="max-width:560px;width:100%">
        <q-card-section class="row items-center">
          <div class="text-h6">新建团队</div>
          <q-space />
          <q-btn flat round dense icon="close" v-close-popup />
        </q-card-section>
        <q-separator />
        <q-card-section>
          <q-form @submit.prevent="submitCreate">
            <q-input v-model="form.name" label="团队名称" outlined dense :rules="[v=>!!v||'必填']" class="q-mb-md" />
            <q-input v-model="form.description" type="textarea" label="描述" outlined dense autogrow class="q-mb-md" />
            <q-select
              v-model="form.member_ids"
              label="团队成员"
              outlined
              dense
              :options="userOptions"
              emit-value
              map-options
              option-value="id"
              option-label="nickname"
              multiple
              use-chips
              stack-label
              clearable
              use-input
              @filter="filterUsers"
            >
              <template v-slot:no-option>
                <q-item>
                  <q-item-section class="text-grey">
                    无可用用户
                  </q-item-section>
                </q-item>
              </template>
            </q-select>
            <div class="row justify-end q-gutter-sm q-mt-md">
              <q-btn outline color="red" label="取消" v-close-popup />
              <q-btn outline color="primary" label="创建" type="submit" :loading="creating" />
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'

const $q = useQuasar()
const router = useRouter()
const loading = ref(false)
const rows = ref([])
const total = ref(0)

// 权限控制
const canCreate = ref(true)
const canDelete = ref(true)

const columns = [
  { name: 'id', label: 'ID', field: 'id', align: 'left', style: 'width:80px' },
  { name: 'name', label: '名称', field: 'name', align: 'left' },
  { name: 'description', label: '描述', field: 'description', align: 'left' },
  { name: 'member_count', label: '成员数', field: 'member_count', align: 'center', style: 'width:100px' },
  { name: 'online_count', label: '在线成员', field: 'online_count', align: 'center', style: 'width:100px' },
  { name: 'created_at', label: '创建时间', field: 'created_at', align: 'left' },
  { name: 'actions', label: '操作', field: 'actions', align: 'left', style: 'width:180px' },
]

async function fetchRows(){
  loading.value = true
  try{
    const { data } = await api.get('/teams/', { params: { page:1, page_size:100 } })
    rows.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

// 加载用户列表
async function loadUsers(){
  try{
    const { data } = await api.get('/users/')
    allUsers.value = data.items || data
    userOptions.value = allUsers.value
  } catch(e){
    console.error('加载用户列表失败:', e)
  }
}

// 过滤用户
function filterUsers(val, update){
  update(() => {
    if (val === '') {
      userOptions.value = allUsers.value
    } else {
      const needle = val.toLowerCase()
      userOptions.value = allUsers.value.filter(
        user => user.nickname?.toLowerCase().includes(needle) || user.username?.toLowerCase().includes(needle)
      )
    }
  })
}

const openCreate = ref(false)
const creating = ref(false)
const form = ref({ name: '', description: '', member_ids: [] })

// 用户选项
const userOptions = ref([])
const allUsers = ref([])

async function submitCreate(){
  creating.value = true
  try{
    await api.post('/teams/', form.value)
    openCreate.value = false
    form.value = { name: '', description: '', member_ids: [] }
    await fetchRows()
    $q.notify({ type:'positive', icon:'check_circle', message:'团队已创建' })
  } catch(e) {
    const msg = e?.response?.data?.detail || '创建失败'
    $q.notify({ type:'negative', icon:'error', message: msg })
  } finally {
    creating.value = false
  }
}

function goMembers(row){
  router.push({ name: 'teams-members', query: { teamId: row.id } })
}

function confirmDelete(row) {
  $q.dialog({
    title: '确认删除',
    message: `确定要删除团队 "${row.name}" 吗？此操作将删除团队及其所有成员关联。`,
    cancel: {
      label: '取消',
      flat: true,
      color: 'grey'
    },
    ok: {
      label: '删除',
      flat: true,
      color: 'negative'
    },
    persistent: true
  }).onOk(async () => {
    await deleteTeam(row)
  })
}

async function deleteTeam(row) {
  try {
    await api.delete(`/teams/${row.id}`)
    await fetchRows()
    $q.notify({
      type: 'positive',
      icon: 'check_circle',
      message: '团队已删除'
    })
  } catch (e) {
    const msg = e?.response?.data?.detail || '删除失败'
    $q.notify({
      type: 'negative',
      icon: 'error',
      message: msg
    })
  }
}

onMounted(async () => {
  await fetchRows()
  await loadUsers()
  
  try {
    const { data } = await api.get('/auth/permissions')
    canCreate.value = data.includes('teams.create')
    canDelete.value = data.includes('teams.delete')
  } catch {
    canCreate.value = true // 后端未启用权限时兜底展示
    canDelete.value = true
  }
})
</script>
