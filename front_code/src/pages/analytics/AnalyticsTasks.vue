<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="text-h6">任务统计</div>
      <q-space />
      <div class="q-gutter-sm">
        <q-btn
          v-if="hasExportPermission"
          outline
          color="primary"
          icon="download"
          label="导出数据"
          @click="exportData"
          :loading="exporting"
        />
        <q-btn
          v-if="hasDeletePermission"
          outline
          color="negative"
          icon="delete"
          label="清理数据"
          @click="confirmDelete"
          :loading="deleting"
        />
      </div>
    </div>

    <div class="row q-col-gutter-md q-mb-md">
      <!-- 任务概览统计 -->
      <div class="col-12">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">任务概览</div>
            <div class="row q-col-gutter-md">
              <div class="col-12 col-sm-6 col-md-3">
                <q-card flat class="bg-primary-1">
                  <q-card-section class="text-center">
                    <div class="text-h4 text-primary">{{ analyticsData.summary?.total_tasks || 0 }}</div>
                    <div class="text-caption">总任务数</div>
                  </q-card-section>
                </q-card>
              </div>
              <div class="col-12 col-sm-6 col-md-3">
                <q-card flat class="bg-positive-1">
                  <q-card-section class="text-center">
                    <div class="text-h4 text-positive">{{ analyticsData.summary?.completed_tasks || 0 }}</div>
                    <div class="text-caption">已完成</div>
                  </q-card-section>
                </q-card>
              </div>
              <div class="col-12 col-sm-6 col-md-3">
                <q-card flat class="bg-warning-1">
                  <q-card-section class="text-center">
                    <div class="text-h4 text-warning">{{ analyticsData.summary?.overdue_tasks || 0 }}</div>
                    <div class="text-caption">逾期任务</div>
                  </q-card-section>
                </q-card>
              </div>
              <div class="col-12 col-sm-6 col-md-3">
                <q-card flat class="bg-info-1">
                  <q-card-section class="text-center">
                    <div class="text-h4 text-info">{{ analyticsData.summary?.completion_rate || 0 }}%</div>
                    <div class="text-caption">完成率</div>
                  </q-card-section>
                </q-card>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- 任务状态分布 -->
      <div class="col-12 col-md-6">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">任务状态分布</div>
            <div class="chart-container">
              <canvas ref="statusChart"></canvas>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- 任务优先级分布 -->
      <div class="col-12 col-md-6">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">任务优先级分布</div>
            <div class="chart-container">
              <canvas ref="priorityChart"></canvas>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- 任务完成趋势 -->
    <q-card flat bordered>
      <q-card-section>
        <div class="text-subtitle1 q-mb-md">任务完成趋势</div>
        <div class="chart-container">
          <canvas ref="trendChart"></canvas>
        </div>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useQuasar } from 'quasar'
import Chart from 'chart.js/auto'
import { api } from 'boot/axios'
import { useAuthStore } from '../../stores/auth'

const $q = useQuasar()
const authStore = useAuthStore()

// 图表引用
const statusChart = ref(null)
const priorityChart = ref(null)
const trendChart = ref(null)

// 加载状态
const loading = ref(false)
const exporting = ref(false)
const deleting = ref(false)

// 数据
const analyticsData = ref({
  status_distribution: [],
  priority_distribution: [],
  weekly_completion_trend: [],
  summary: {
    total_tasks: 0,
    completed_tasks: 0,
    overdue_tasks: 0,
    completion_rate: 0
  }
})

// 权限检查
const hasExportPermission = computed(() => authStore.hasPermission('analytics.export'))
const hasDeletePermission = computed(() => authStore.hasPermission('analytics.delete'))

// 加载数据
async function loadAnalyticsData() {
  loading.value = true
  try {
    const response = await api.get('/analytics/tasks')
    analyticsData.value = response.data
    updateCharts()
  } catch (error) {
    console.error('加载任务分析数据失败:', error)
    $q.notify({
      type: 'negative',
      message: '加载数据失败',
      position: 'top'
    })
  } finally {
    loading.value = false
  }
}

// 更新图表
function updateCharts() {
  updateStatusChart()
  updatePriorityChart()
  updateTrendChart()
}

function updateStatusChart() {
  if (!statusChart.value) return

  const ctx = statusChart.value.getContext('2d')
  if (window.taskStatusChartInstance) {
    window.taskStatusChartInstance.destroy()
  }

  window.taskStatusChartInstance = new Chart(ctx, {
    type: 'pie',
    data: {
      labels: analyticsData.value.status_distribution.map(item => item.status),
      datasets: [{
        data: analyticsData.value.status_distribution.map(item => item.count),
        backgroundColor: [
          '#4caf50', // 绿色 - 完成
          '#ff9800', // 橙色 - 进行中
          '#f44336', // 红色 - 暂停
          '#9e9e9e'  // 灰色 - 取消
        ]
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom'
        }
      }
    }
  })
}

function updatePriorityChart() {
  if (!priorityChart.value) return

  const ctx = priorityChart.value.getContext('2d')
  if (window.taskPriorityChartInstance) {
    window.taskPriorityChartInstance.destroy()
  }

  window.taskPriorityChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: analyticsData.value.priority_distribution.map(item => item.priority || '未设置'),
      datasets: [{
        data: analyticsData.value.priority_distribution.map(item => item.count),
        backgroundColor: [
          '#f44336', // 高
          '#ff9800', // 中
          '#4caf50', // 低
          '#9e9e9e'  // 未设置
        ]
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom'
        }
      }
    }
  })
}

function updateTrendChart() {
  if (!trendChart.value) return

  const ctx = trendChart.value.getContext('2d')
  if (window.taskTrendChartInstance) {
    window.taskTrendChartInstance.destroy()
  }

  window.taskTrendChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: analyticsData.value.weekly_completion_trend.map(item => {
        const date = new Date(item.week)
        return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
      }),
      datasets: [{
        label: '完成任务数量',
        data: analyticsData.value.weekly_completion_trend.map(item => item.count),
        borderColor: '#4caf50',
        backgroundColor: 'rgba(76, 175, 80, 0.1)',
        tension: 0.4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  })
}

// 导出数据
async function exportData() {
  exporting.value = true
  try {
    const response = await api.get('/analytics/export/tasks', {
      responseType: 'blob'
    })

    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'tasks_analytics.json')
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)

    $q.notify({
      type: 'positive',
      message: '数据导出成功',
      position: 'top'
    })
  } catch (error) {
    console.error('导出数据失败:', error)
    $q.notify({
      type: 'negative',
      message: '导出数据失败',
      position: 'top'
    })
  } finally {
    exporting.value = false
  }
}

// 确认删除数据
function confirmDelete() {
  $q.dialog({
    title: '确认操作',
    message: '确定要清理任务分析数据吗？此操作不可恢复。',
    cancel: true,
    persistent: true
  }).onOk(async () => {
    await deleteData()
  })
}

// 删除数据
async function deleteData() {
  deleting.value = true
  try {
    await api.delete('/analytics/data/temp_data')
    $q.notify({
      type: 'positive',
      message: '数据清理成功',
      position: 'top'
    })
    // 重新加载数据
    await loadAnalyticsData()
  } catch (error) {
    console.error('清理数据失败:', error)
    $q.notify({
      type: 'negative',
      message: '清理数据失败',
      position: 'top'
    })
  } finally {
    deleting.value = false
  }
}

// 生命周期
onMounted(() => {
  loadAnalyticsData()
})
</script>

<style scoped>
.chart-container {
  height: 300px;
  position: relative;
}
</style>
