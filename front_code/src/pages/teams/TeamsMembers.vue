<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-col-gutter-md q-mb-md">
      <div class="col-auto text-h6">团队成员</div>
      <div class="col-auto"><TeamSelector @change="onTeamChange" /></div>
      <q-space />
      <q-btn v-if="authStore.hasPermission('teams.update')" outline color="primary" icon="person_add" label="添加成员" @click="openAdd=true" />
    </div>
    <q-card flat bordered>
      <q-table :rows="rows" :columns="columns" row-key="user_id" flat :loading="loading">
        <template #body-cell-role="props">
          <q-td :props="props">
            <template v-if="allRoleNames(props.row).length">
              <q-chip v-for="name in allRoleNames(props.row)" :key="name" square dense color="indigo-1" text-color="indigo-9" class="q-mr-xs">
                {{ name }}
              </q-chip>
            </template>
            <span v-else>无角色</span>
          </q-td>
        </template>
        <template #body-cell-online="props">
          <q-td :props="props">
            <q-icon :name="isOnline(props.row) ? 'lens' : 'radio_button_unchecked'" :color="isOnline(props.row) ? 'positive' : 'grey-5'" size="14px" />
          </q-td>
        </template>
        <template #body-cell-actions="props">
          <q-td :props="props">
            <q-btn v-if="authStore.hasPermission('teams.update')" flat dense color="negative" icon="person_remove" label="移除" @click="removeMember(props.row)" />
          </q-td>
        </template>
        <template #no-data>
          <div class="q-pa-lg text-grey">暂无成员</div>
        </template>
      </q-table>
    </q-card>

    <q-dialog v-model="openAdd">
      <q-card style="max-width:560px;width:100%">
        <q-card-section class="row items-center">
          <div class="text-h6">添加成员</div>
          <q-space />
          <q-btn flat round dense icon="close" v-close-popup />
        </q-card-section>
        <q-separator />
        <q-card-section>
          <q-form @submit.prevent="submitAdd">
            <q-select
              v-model="selectedUserIds"
              :options="userOptions"
              outlined
              dense
              multiple
              use-chips
              use-input
              input-debounce="300"
              @filter="filterUsers"
              emit-value
              map-options
              option-label="label"
              option-value="value"
              :loading="loadingUsers"
              clearable
              label="选择成员（支持多选）"
              hint="按住 Ctrl/Cmd 可以选择多个成员"
            />
            <div class="row justify-end q-gutter-sm q-mt-md">
              <q-btn outline color="red" label="取消" v-close-popup />
              <q-btn outline color="primary" label="批量添加" type="submit" :loading="adding" />
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { LocalStorage } from 'quasar'
import { useTeamStore } from 'stores/team/useTeamStore'
import TeamSelector from 'components/TeamSelector.vue'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'
import { useAuthStore } from 'stores/auth'

const route = useRoute()
const router = useRouter()
const store = useTeamStore()
const authStore = useAuthStore()

const teamId = computed(() => store.currentTeamId)

const loading = ref(false)
const rows = ref([])
const columns = [
  { name:'user_id', label:'用户ID', field:'user_id', align:'left', style:'width:100px' },
  { name:'username', label:'用户名', field:'username', align:'left' },
  { name:'nickname', label:'昵称', field:'nickname', align:'left' },
  { name:'role', label:'角色', field:'role', align:'left' },
  { name:'online', label:'在线', field:'online', align:'center', style:'width:100px' },
  { name:'actions', label:'操作', field:'actions', align:'right', style:'width:120px' }
]
const $q = useQuasar()
const openAdd = ref(false)
const adding = ref(false)
const selectedUserIds = ref([])
const userOptions = ref([])
const loadingUsers = ref(false)

async function ensureTeam() {
  // 1. URL 优先
  let id = route.query.teamId
  // 2. 本地最近
  if (!id) id = LocalStorage.getItem('lastTeamId')
  // 3. 列表第一个
  if (!id) {
    const list = store.teams.length ? store.teams : await store.fetchTeams()
    id = list[0]?.id
  }
  if (id && String(id) !== String(store.currentTeamId)) {
    store.setCurrentTeam(id)
  }
  // 将 teamId 反映到 URL 便于分享/刷新
  if (id && route.query.teamId !== String(id)) {
    router.replace({ query: { ...route.query, teamId: String(id) } })
  }
}

function reload() {
  if (!teamId.value) return
  loadMembers()
}

onMounted(async () => {
  // 始终从后端刷新团队列表，避免默认数据干扰
  await store.fetchTeams()
  await ensureTeam()
  reload()
})

async function loadMembers(){
  loading.value = true
  try{
    const { data } = await api.get(`/teams/${teamId.value}/members`)
    rows.value = data
  } finally {
    loading.value = false
  }
}

async function submitAdd(){
  adding.value = true
  try{
    if (!selectedUserIds.value || selectedUserIds.value.length === 0) {
      $q.notify({ type:'warning', icon:'warning', message:'请至少选择一个用户' })
      return
    }
    // 使用批量添加接口
    const result = await api.post(`/teams/${teamId.value}/members/batch`, { user_ids: selectedUserIds.value })
    openAdd.value = false
    selectedUserIds.value = []
    await loadMembers()
    
    // 显示添加结果
    if (result.data.added_count > 0) {
      $q.notify({ 
        type:'positive', 
        icon:'check_circle', 
        message: `成功添加 ${result.data.added_count} 个成员`,
        caption: result.data.errors.length > 0 ? `部分失败: ${result.data.errors.join(', ')}` : undefined
      })
    } else {
      $q.notify({ 
        type:'warning', 
        icon:'warning', 
        message: '没有成员被添加',
        caption: result.data.errors.join(', ')
      })
    }
  } catch(e){
    const msg = e?.response?.data?.detail || '添加失败'
    $q.notify({ type:'negative', icon:'error', message: msg })
  } finally {
    adding.value = false
  }
}

async function removeMember(row){
  try{
    await api.delete(`/teams/${teamId.value}/members/${row.user_id}`)
    await loadMembers()
    $q.notify({ type:'positive', icon:'check_circle', message:'已移除成员' })
  } catch(e){
    const msg = e?.response?.data?.detail || '移除失败'
    $q.notify({ type:'negative', icon:'error', message: msg })
  }
}

function onTeamChange(){
  reload()
}

function filterUsers(val, update){
  update(async () => {
    loadingUsers.value = true
    try {
      const { data } = await api.get('/users/', { params: { page:1, page_size:20, q: val || undefined }})
      userOptions.value = data.items.map(u => ({
        label: u.nickname ? `${u.username}（${u.nickname}）` : u.username,
        value: u.id,
      }))
    } finally {
      loadingUsers.value = false
    }
  })
}

// 在线状态辅助函数
function isOnline(row) {
  return row.is_online || false
}

function allRoleNames(row) {
  if (!row) return []
  // 后端已返回角色名称数组，直接使用
  return Array.isArray(row.roles) ? row.roles : []
}
</script>
