<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="text-h6">任务甘特图</div>
      <q-space />
      <q-btn outline color="primary" label="刷新" icon="refresh" @click="refresh" />
    </div>

    <q-card flat bordered>
      <q-card-section>
        <div class="text-center text-grey-6 q-pa-xl">
          <q-icon name="timeline" size="4rem" class="q-mb-md" />
          <div class="text-h6 q-mb-sm">任务甘特图功能</div>
          <div class="text-body1">正在开发中...</div>
          <div class="text-caption">将显示任务的时间线、依赖关系和进度跟踪</div>
        </div>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup>
import { onMounted } from 'vue'

// 方法
function refresh() {
  // TODO: 实现刷新逻辑
  console.log('刷新甘特图')
}

onMounted(() => {
  // TODO: 加载甘特图数据
})
</script>