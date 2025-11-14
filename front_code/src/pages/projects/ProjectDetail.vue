<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <q-btn flat icon="arrow_back" @click="$router.push('/projects')" />
      <div class="text-h6 q-ml-md">{{ project?.name || "项目详情" }}</div>
      <q-space />
    </div>

    <q-tabs v-model="tab" class="text-grey-8" align="left">
      <q-tab name="details" label="详情" />
      <q-tab name="files" label="文件" />
      <q-tab name="gantt" label="甘特图" />
      <q-tab name="milestones" label="里程碑" />
      <q-tab name="analytics" label="统计分析" />



    </q-tabs>

    <q-tab-panels v-model="tab" animated swipeable vertical class="q-mt-md">
      <q-tab-panel name="details">
        <router-view />
      </q-tab-panel>
      <q-tab-panel name="gantt">
        <router-view />
      </q-tab-panel>
      <q-tab-panel name="members">
        <router-view />
      </q-tab-panel>
      <q-tab-panel name="files">
        <router-view />
      </q-tab-panel>
      <q-tab-panel name="settings">
        <router-view />
      </q-tab-panel>
    </q-tab-panels>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { useRoute } from "vue-router"
import { api } from "boot/axios"

const route = useRoute()
const tab = ref("details")
const project = ref(null)

async function loadProject() {
  try {
    const { data } = await api.get(`/projects/${route.params.id}`)
    project.value = data
  } catch (error) {
    console.error("加载项目失败:", error)
  }
}

onMounted(loadProject)
</script>
