<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="text-h6">项目统计</div>
      <q-space />
      <q-btn flat dense icon="refresh" @click="loadTasks" />
    </div>

    <div v-if="loading">加载中…</div>
    <div v-else>
      <div class="row q-col-gutter-md">
        <div class="col-12 col-md-4">
          <q-card>
            <q-card-section>
              <div class="text-subtitle2">任务总数</div>
              <div class="text-h5">{{ stats.total }}</div>
            </q-card-section>
          </q-card>
        </div>
        <div class="col-12 col-md-4">
          <q-card>
            <q-card-section>
              <div class="text-subtitle2">未完成</div>
              <div class="text-h5">{{ stats.incomplete }}</div>
            </q-card-section>
          </q-card>
        </div>
        <div class="col-12 col-md-4">
          <q-card>
            <q-card-section>
              <div class="text-subtitle2">已完成</div>
              <div class="text-h5">{{ stats.completed }}</div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <q-separator class="q-my-md" />

      <div class="text-subtitle1 q-mb-sm">按状态统计</div>
      <q-list bordered>
        <q-item v-for="(cnt, status) in byStatus" :key="status">
          <q-item-section>{{ status }}</q-item-section>
          <q-item-section side>
            <q-badge :label="cnt" color="primary" />
          </q-item-section>
        </q-item>
      </q-list>

      <q-separator class="q-my-md" />

      <div class="text-subtitle1 q-mb-sm">按负责人统计</div>
      <q-list bordered>
        <q-item v-for="(cnt, assignee) in byAssignee" :key="assignee">
          <q-item-section>{{ assignee }}</q-item-section>
          <q-item-section side>
            <q-badge :label="cnt" color="secondary" />
          </q-item-section>
        </q-item>
      </q-list>
    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'

const route = useRoute()
const $q = useQuasar()
const loading = ref(false)
const tasks = ref([])
const stats = ref({ total: 0, incomplete: 0, completed: 0 })
const byStatus = ref({})
const byAssignee = ref({})

async function loadTasks(){
  loading.value = true
  try{
    const { data } = await api.get('/tasks/', { params: { project_id: route.params.id, page_size: 200 } })
    tasks.value = data.items || []
    computeStats()
  }catch(e){
    console.error('加载任务失败', e)
    $q.notify({ type: 'negative', message: '加载任务失败', position: 'top' })
    tasks.value = []
  }finally{
    loading.value = false
  }
}

function computeStats(){
  stats.value.total = tasks.value.length
  stats.value.completed = tasks.value.filter(t => t.status === '已完成' || t.status === 'completed').length
  stats.value.incomplete = stats.value.total - stats.value.completed

  const s = {}
  const a = {}
  for(const t of tasks.value){
    const st = t.status || '未知'
    s[st] = (s[st] || 0) + 1
    if(Array.isArray(t.assignees) && t.assignees.length){
      for(const as of t.assignees){
        const name = as.nickname || as.username || ('#' + as.id)
        a[name] = (a[name] || 0) + 1
      }
    } else {
      a['未分配'] = (a['未分配'] || 0) + 1
    }
  }
  byStatus.value = s
  byAssignee.value = a
}

onMounted(loadTasks)
</script>
