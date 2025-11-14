<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="text-h6">任务统计分析</div>
      <q-space />
      <q-btn outline color="primary" label="刷新" icon="refresh" @click="refresh" />
    </div>

    <div class="row q-col-gutter-md q-mb-md">
      <!-- 统计卡片 -->
      <div class="col-12 col-md-3">
        <q-card flat bordered>
          <q-card-section class="text-center">
            <q-icon name="assignment" size="2rem" color="primary" class="q-mb-sm" />
            <div class="text-h6">{{ stats.totalTasks }}</div>
            <div class="text-caption">总任务数</div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-md-3">
        <q-card flat bordered>
          <q-card-section class="text-center">
            <q-icon name="check_circle" size="2rem" color="positive" class="q-mb-sm" />
            <div class="text-h6">{{ stats.completedTasks }}</div>
            <div class="text-caption">已完成</div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-md-3">
        <q-card flat bordered>
          <q-card-section class="text-center">
            <q-icon name="schedule" size="2rem" color="warning" class="q-mb-sm" />
            <div class="text-h6">{{ stats.inProgressTasks }}</div>
            <div class="text-caption">进行中</div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-md-3">
        <q-card flat bordered>
          <q-card-section class="text-center">
            <q-icon name="pending" size="2rem" color="negative" class="q-mb-sm" />
            <div class="text-h6">{{ stats.pendingTasks }}</div>
            <div class="text-caption">待处理</div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <q-card flat bordered>
      <q-card-section>
        <div class="text-center text-grey-6 q-pa-xl">
          <q-icon name="bar_chart" size="4rem" class="q-mb-md" />
          <div class="text-h6 q-mb-sm">任务统计分析功能</div>
          <div class="text-body1">正在开发中...</div>
          <div class="text-caption">将显示任务完成率、效率统计、趋势分析等</div>
        </div>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup>
import { reactive, onMounted } from 'vue'

// 数据
const stats = reactive({
  totalTasks: 0,
  completedTasks: 0,
  inProgressTasks: 0,
  pendingTasks: 0
})

// 方法
function refresh() {
  // TODO: 实现刷新逻辑
  console.log('刷新统计数据')
  loadStats()
}

async function loadStats() {
  // TODO: 加载统计数据
  console.log('加载任务统计数据')
}

onMounted(() => {
  loadStats()
})
</script>