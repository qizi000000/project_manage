<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="text-h6">角色权限</div>
      <q-space />
      <q-btn v-if="canCreateRole" outline color="primary" icon="add" label="新建角色" @click="openCreate = true" />
    </div>

    <div class="row q-col-gutter-md">
      <!-- 角色侧栏 -->
      <div class="col-12 col-md-3">
        <q-card flat bordered>
          <q-card-section class="text-subtitle2">角色列表</q-card-section>
          <q-separator />
          <q-card-section>
            <q-input v-model="roleSearch" dense outlined label="搜索角色" clearable debounce="200" />
          </q-card-section>
          <q-separator />
          <q-list separator>
            <q-item v-for="r in filteredRoles" :key="r.id" clickable :active="r.id===activeRoleId" @click="selectRole(r)">
              <q-item-section>
                <div class="row items-center">
                  <div class="ellipsis">{{ r.name }}</div>
                  <q-badge v-if="r.is_superadmin" color="deep-orange" class="q-ml-sm">超级</q-badge>
                </div>
              </q-item-section>
              <q-item-section side>
                <q-btn v-if="canDeleteRole && !r.is_superadmin" flat dense round icon="delete" color="red" @click.stop="askRemoveRole(r)" />
              </q-item-section>
            </q-item>
            <q-item v-if="!filteredRoles.length">
              <q-item-section class="text-grey">无匹配角色</q-item-section>
            </q-item>
          </q-list>
        </q-card>
      </div>

      <!-- 权限主面板 -->
      <div class="col-12 col-md-9">
        <q-card flat bordered class="relative-position">
          <q-card-section class="row items-center">
            <div class="text-subtitle2">权限分配</div>
            <q-space />
            <div class="text-caption q-mr-md">已选 {{ selectedCount }} / 共 {{ totalCount }}</div>
          </q-card-section>
          <q-separator />
          <q-card-section>
            <div v-if="!activeRoleId" class="text-grey">请选择左侧角色</div>
            <template v-else>
              <q-banner v-if="isActiveSuper" dense rounded class="bg-orange-1 text-orange-10 q-mb-md">
                超级管理员拥有全部权限，无法编辑。
              </q-banner>
              <div class="row items-center q-col-gutter-md q-mb-sm">
                <div class="col-12 col-md-5">
                  <q-input v-model="permSearch" dense outlined label="搜索权限（名称或编码）" clearable debounce="200" />
                </div>
                <div class="col-6 col-md-3">
                  <q-toggle v-model="onlySelected" label="仅看已选" :disable="isActiveSuper" />
                </div>
                <div class="col-6 col-md-4 text-right">
                  <q-btn flat dense icon="unfold_more" label="展开全部" class="q-mr-sm" @click="expandAll=true" />
                  <q-btn flat dense icon="unfold_less" label="折叠全部" @click="expandAll=false" />
                </div>
              </div>

              <q-separator class="q-mb-md" />

              <q-expansion-item
                v-for="g in filteredGroups"
                :key="g.group"
                expand-separator
                :label="g.group"
                :model-value="expandAll"
              >
                <template #header>
                  <div class="row items-center full-width">
                    <div class="col">
                      <div class="text-subtitle2">{{ g.group }}</div>
                    </div>
                    <div class="col-auto row items-center">
                      <q-checkbox
                        :model-value="isGroupChecked(g)"
                        :indeterminate="isGroupIndeterminate(g)"
                        @update:model-value="val => toggleGroup(g, val)"
                        :disable="isActiveSuper"
                        label="全选分组"
                      />
                    </div>
                  </div>
                </template>
                <div class="row q-col-gutter-sm q-pt-sm">
                  <div v-for="p in g.items" :key="p.id" class="col-12 col-sm-6 col-md-4">
                    <q-checkbox v-model="selected" :val="p.id" :label="p.name" :disable="isActiveSuper" />
                    <div class="text-caption text-grey-7">{{ p.code }}</div>
                  </div>
                </div>
              </q-expansion-item>

              <div v-if="!filteredGroups.length" class="text-grey">无匹配权限</div>
            </template>
          </q-card-section>

          <div class="save-footer q-pa-sm" v-if="activeRoleId">
            <q-btn unelevated color="primary" class="full-width" :disable="saving || isActiveSuper || !canUpdateRole" :loading="saving" label="保存" @click="savePermissions" />
          </div>
        </q-card>
      </div>
    </div>

    <!-- 新建角色 -->
    <q-dialog v-model="openCreate" persistent :maximized="$q.screen.lt.md">
      <q-card style="max-width: 500px; width: 100%">
        <q-card-section class="row items-center">
          <div class="text-h6">新建角色</div>
          <q-space />
          <q-btn flat round dense icon="close" v-close-popup />
        </q-card-section>
        <q-separator />
        <q-card-section>
          <q-form @submit.prevent="submitCreate">
            <q-input v-model="createForm.name" label="角色名称" outlined dense :rules="[v=>!!v||'必填']" />
            <q-input v-model="createForm.remark" label="备注" outlined dense class="q-mt-md" />
            <div class="row justify-end q-gutter-sm q-mt-md">
              <q-btn outline color="red" label="取消" v-close-popup />
              <q-btn outline color="primary" type="submit" :loading="creating" label="创建" />
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- 删除角色确认 -->
    <q-dialog v-model="confirmDelete.open">
      <q-card style="max-width: 420px; width: 100%">
        <q-card-section class="text-h6">删除角色</q-card-section>
        <q-card-section>确认删除角色“{{ confirmDelete.role?.name }}”？该操作不可撤销。</q-card-section>
        <q-card-actions align="right">
          <q-btn flat color="grey" label="取消" v-close-popup />
          <q-btn outline color="red" label="删除" @click="doRemoveRole" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'
import { useAuthStore } from '../../stores/auth'

const roles = ref([])
const activeRoleId = ref(null)
const groups = ref([])
const selected = ref([])
const saving = ref(false)
const $q = useQuasar()
const authStore = useAuthStore()
const roleSearch = ref('')
const permSearch = ref('')
const onlySelected = ref(false)
const expandAll = ref(true)

// 权限检查
const canCreateRole = computed(() => authStore.hasPermission('roles.create'))
const canUpdateRole = computed(() => authStore.hasPermission('roles.update'))
const canDeleteRole = computed(() => authStore.hasPermission('roles.delete'))

async function loadRoles() {
  const { data } = await api.get('/roles/')
  roles.value = data
}

async function loadGroups() {
  const { data } = await api.get('/permissions/grouped')
  groups.value = data
}

async function selectRole(r) {
  activeRoleId.value = r.id
  if (r.is_superadmin) {
    // 超级管理员拥有全部权限（只读效果）
    const ids = []
    groups.value.forEach(g => g.items.forEach(p => ids.push(p.id)))
    selected.value = ids
  } else {
    const { data } = await api.get(`/roles/${r.id}/permissions`)
    selected.value = data
  }
}

async function savePermissions() {
  if (!activeRoleId.value) return
  saving.value = true
  try {
    await api.put(`/roles/${activeRoleId.value}/permissions`, { permission_ids: selected.value })
  $q.notify({ type: 'positive', message: '保存成功', icon: 'check_circle', position: 'bottom-right', timeout: 2000 })
  } finally {
    saving.value = false
  }
}

const openCreate = ref(false)
const creating = ref(false)
const createForm = ref({ name: '', remark: '' })

async function submitCreate() {
  creating.value = true
  try {
    const params = new URLSearchParams()
    params.set('name', createForm.value.name)
    if (createForm.value.remark) params.set('remark', createForm.value.remark)
    await api.post('/roles/', null, { params })
    openCreate.value = false
    createForm.value = { name: '', remark: '' }
    await loadRoles()
  $q.notify({ type: 'positive', message: '角色已创建', icon: 'add_circle', position: 'bottom-right', timeout: 2000 })
  } finally {
    creating.value = false
  }
}

onMounted(async () => {
  await loadRoles()
  await loadGroups()
  // 默认选中管理员角色（优先超级管理员，其次名称为“管理员”，否则第一个）
  const adminRole = roles.value.find(r => r.is_superadmin) || roles.value.find(r => r.name === '管理员') || roles.value[0]
  if (adminRole) {
    await selectRole(adminRole)
  }
})

const isActiveSuper = computed(() => {
  const r = roles.value.find(x => x.id === activeRoleId.value)
  return !!(r && r.is_superadmin)
})

const filteredRoles = computed(() => {
  const kw = roleSearch.value.trim().toLowerCase()
  if (!kw) return roles.value
  return roles.value.filter(r => r.name.toLowerCase().includes(kw))
})

const filteredGroups = computed(() => {
  const kw = permSearch.value.trim().toLowerCase()
  return groups.value
    .map(g => ({
      group: g.group,
      items: g.items.filter(p => {
        const ok = !kw || p.name.toLowerCase().includes(kw) || (p.code || '').toLowerCase().includes(kw)
        const selOk = !onlySelected.value || selected.value.includes(p.id)
        return ok && selOk
      }),
    }))
    .filter(g => g.items.length > 0)
})

const totalCount = computed(() => groups.value.reduce((acc, g) => acc + g.items.length, 0))
const selectedCount = computed(() => selected.value.length)

function isGroupChecked(g) {
  const ids = g.items.map(p => p.id)
  if (!ids.length) return false
  return ids.every(id => selected.value.includes(id))
}

function isGroupIndeterminate(g) {
  const ids = g.items.map(p => p.id)
  if (!ids.length) return false
  const hit = ids.filter(id => selected.value.includes(id)).length
  return hit > 0 && hit < ids.length
}

function toggleGroup(g, val) {
  const ids = g.items.map(p => p.id)
  if (val) {
    // add all
    const set = new Set(selected.value)
    ids.forEach(id => set.add(id))
    selected.value = Array.from(set)
  } else {
    // remove all
    const set = new Set(selected.value)
    ids.forEach(id => set.delete(id))
    selected.value = Array.from(set)
  }
}

const confirmDelete = ref({ open: false, role: null })
function askRemoveRole(r) {
  confirmDelete.value.open = true
  confirmDelete.value.role = r
}
async function doRemoveRole() {
  const r = confirmDelete.value.role
  confirmDelete.value.open = false
  if (!r) return
  try {
    await api.delete(`/roles/${r.id}`)
    if (activeRoleId.value === r.id) {
      activeRoleId.value = null
      selected.value = []
    }
    await loadRoles()
  $q.notify({ type: 'positive', message: '角色已删除', icon: 'delete', position: 'bottom-right', timeout: 2000 })
  } catch (e) {
  console.error('删除角色失败', e)
  $q.notify({ type: 'negative', message: '删除失败', icon: 'error', position: 'bottom-right', timeout: 2500 })
  }
}
</script>

<style scoped>
.save-footer {
  position: sticky;
  bottom: 0;
  background: rgba(255,255,255,0.9);
}
</style>
