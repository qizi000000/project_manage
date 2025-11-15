<template>
  <q-page class="q-pt-md">
    <div class="row items-center q-pb-md">
      <q-btn flat icon="arrow_back" @click="$router.push('/projects')" />
      
      <q-tabs v-model="tab" class="text-grey-8" align="right" dense>
        <q-tab name="details" label="详情" />
       
        <q-tab name="gantt" label="甘特图" />
        <q-tab name="milestones" label="里程碑" />
       
      </q-tabs>
    </div>

    

    <q-tab-panels v-model="tab"  class="">
      <q-tab-panel name="details">
        <router-view />
      </q-tab-panel>
      <q-tab-panel name="members">
        <router-view />
      </q-tab-panel>
      <q-tab-panel name="files">
        <router-view />
      </q-tab-panel>
      <q-tab-panel name="gantt">
        <router-view />
      </q-tab-panel>
      <q-tab-panel name="milestones">
        <router-view />
      </q-tab-panel>
      
    </q-tab-panels>
  </q-page>
</template>

<script setup>
import { ref, onMounted, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import { api } from "boot/axios"

const route = useRoute()
const router = useRouter()
const tab = ref("details")
const project = ref(null)

// 标签页路由映射
const tabRoutes = {
  details: 'project-details',
  gantt: 'project-gantt',
  milestones: 'project-milestones'
}

// 监听标签变化，导航到对应路由
watch(tab, (newTab) => {
  const routeName = tabRoutes[newTab]
  if (routeName) {
    router.push({ name: routeName, params: { id: route.params.id } })
  }
})

// 根据当前路由设置活动标签
function setActiveTab() {
  const currentRoute = route.name
  const tabName = Object.keys(tabRoutes).find(key => tabRoutes[key] === currentRoute)
  if (tabName) {
    tab.value = tabName
  }
}

async function loadProject() {
  try {
    const { data } = await api.get(`/projects/${route.params.id}`)
    project.value = data
  } catch (error) {
    console.error("加载项目失败:", error)
  }
}

onMounted(() => {
  setActiveTab()
  loadProject()
})
</script>
