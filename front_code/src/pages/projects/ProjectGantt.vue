<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="text-h6">项目甘特图</div>
      <q-space />
      <q-select
        v-if="!route.params.id"
        v-model="selectedProject"
        :options="projectOptions"
        option-value="value"
        option-label="label"
        map-options
        emit-value
        label="选择项目"
        class="q-mr-md"
        style="min-width: 200px"
        @update:model-value="onProjectChange"
      />
      <q-btn flat dense icon="refresh" @click="loadTasks" />
    </div>

    <div v-if="loading">加载中…</div>
    <div v-else-if="tasks.length===0" class="text-grey">暂无任务可展示甘特图</div>
    <div v-else class="gantt-wrapper">
      <div class="gantt-grid">
        <div class="gantt-row header">
          <div class="gantt-cell name">任务</div>
          <div class="gantt-cell chart">
            <div class="gantt-scale">
              <div v-for="d in scale" :key="d" class="scale-cell">{{ d }}</div>
            </div>
          </div>
        </div>

        <div v-for="t in tasks" :key="t.id" class="gantt-row">
          <div class="gantt-cell name">{{ t.title }}</div>
          <div class="gantt-cell chart">
            <div class="bar" :style="barStyle(t)"></div>
          </div>
        </div>
      </div>
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
const tasks = ref([])
const loading = ref(false)
const scale = ref([])
const selectedProject = ref(null)
const projectOptions = ref([])
const projectId = ref(route.params.id || null)

function dateToYMD(dt){
  const d = new Date(dt)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

function buildScale(minDate, maxDate){
  const s = []
  const cur = new Date(minDate)
  while(cur <= new Date(maxDate)){
    s.push(`${cur.getFullYear()}-${String(cur.getMonth()+1).padStart(2,'0')}-${String(cur.getDate()).padStart(2,'0')}`)
    cur.setDate(cur.getDate()+1)
  }
  return s
}

function computeRange(tasksList){
  let min = null, max = null
  for(const t of tasksList){
    const start = t.created_at || t.start_date || new Date().toISOString()
    const end = t.due_date || (t.estimated_days ? new Date(new Date(start).getTime()+t.estimated_days*24*3600*1000).toISOString() : start)
    if(!min || new Date(start) < new Date(min)) min = start
    if(!max || new Date(end) > new Date(max)) max = end
    t._gantt_start = start
    t._gantt_end = end
  }
  return [min, max]
}

function barStyle(t){
  if(!scale.value.length) return {}
  const total = scale.value.length
  const startIndex = Math.max(0, scale.value.indexOf(dateToYMD(t._gantt_start)))
  const endIndex = Math.max(startIndex, scale.value.indexOf(dateToYMD(t._gantt_end)))
  const left = (startIndex/total)*100
  const width = ((endIndex - startIndex + 1)/total)*100
  return { left: left + '%', width: Math.max(2, width) + '%'}
}

async function loadProjects(){
  try{
    const { data } = await api.get('/projects/', { params: { page_size: 100 } })
    projectOptions.value = (data.items || []).map(p => ({ label: p.name, value: p.id }))
    if(projectOptions.value.length && !projectId.value){
      selectedProject.value = projectOptions.value[0].value
      projectId.value = selectedProject.value
    }
  }catch(e){
    console.error('加载项目失败', e)
  }
}

function onProjectChange(val){
  projectId.value = val
  loadTasks()
}

async function loadTasks(){
  if(!projectId.value) return
  loading.value = true
  try{
    const { data } = await api.get('/tasks/', { params: { project_id: projectId.value, page_size: 200 } })
    tasks.value = data.items || []
    const [min, max] = computeRange(tasks.value)
    if(min && max){
      scale.value = buildScale(min, max)
    } else {
      scale.value = []
    }
  }catch(e){
    console.error('加载任务失败', e)
    $q.notify({ type: 'negative', message: '加载任务失败', position: 'top' })
    tasks.value = []
  }finally{
    loading.value = false
  }
}

onMounted(async () => {
  if(!route.params.id){
    await loadProjects()
  }
  loadTasks()
})
</script>

<style scoped>
.gantt-wrapper{ overflow:auto }
.gantt-grid{ min-width:800px }
.gantt-row{ display:flex; align-items:center; height:40px; border-bottom:1px solid #eee }
.gantt-row.header{ background:#fafafa; font-weight:600 }
.gantt-cell.name{ width:240px; padding:8px }
.gantt-cell.chart{ flex:1; position:relative; padding:6px 8px }
.gantt-scale{ display:flex; gap:2px }
.scale-cell{ flex:1; font-size:11px; color:#666; text-align:center }
.bar{ position:absolute; height:22px; background:linear-gradient(90deg,#42a5f5,#1e88e5); border-radius:4px }
</style>
