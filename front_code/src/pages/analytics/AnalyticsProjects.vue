<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="text-h6">项目统计</div>
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
      <!-- 项目状态分布 -->
      <div class="col-12 col-md-6">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">项目状态分布</div>
            <div class="chart-container">
              <canvas ref="statusChart"></canvas>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- 项目负责人分布 -->
      <div class="col-12 col-md-6">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">项目负责人分布</div>
            <div class="chart-container">
              <canvas ref="ownerChart"></canvas>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- 项目创建趋势 -->
    <q-card flat bordered>
      <q-card-section>
        <div class="text-subtitle1 q-mb-md">项目创建趋势</div>
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
const ownerChart = ref(null)
const trendChart = ref(null)

// 加载状态
const loading = ref(false)
const exporting = ref(false)
const deleting = ref(false)

// 数据
const analyticsData = ref({
  status_distribution: [],
  owner_distribution: [],
  monthly_trend: []
})

// 权限检查
const hasExportPermission = computed(() => authStore.hasPermission('analytics.export'))
const hasDeletePermission = computed(() => authStore.hasPermission('analytics.delete'))

// 加载数据
async function loadAnalyticsData() {
  loading.value = true
  try {
    const response = await api.get('/analytics/projects')
    analyticsData.value = response.data
    updateCharts()
  } catch (error) {
    console.error('加载项目分析数据失败:', error)
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
  updateOwnerChart()
  updateTrendChart()
}

function updateStatusChart() {
  if (!statusChart.value) return

  const ctx = statusChart.value.getContext('2d')
  if (window.statusChartInstance) {
    window.statusChartInstance.destroy()
  }

  window.statusChartInstance = new Chart(ctx, {
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

function updateOwnerChart() {
  if (!ownerChart.value) return

  const ctx = ownerChart.value.getContext('2d')
  if (window.ownerChartInstance) {
    window.ownerChartInstance.destroy()
  }

  window.ownerChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: analyticsData.value.owner_distribution.map(item => item.owner),
      datasets: [{
        label: '项目数量',
        data: analyticsData.value.owner_distribution.map(item => item.count),
        backgroundColor: '#2196f3'
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

function updateTrendChart() {
  if (!trendChart.value) return

  const ctx = trendChart.value.getContext('2d')
  if (window.trendChartInstance) {
    window.trendChartInstance.destroy()
  }

  window.trendChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: analyticsData.value.monthly_trend.map(item => `${item.month}月`),
      datasets: [{
        label: '项目创建数量',
        data: analyticsData.value.monthly_trend.map(item => item.count),
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
    const response = await api.get('/analytics/export/projects', {
      responseType: 'blob'
    })

    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'projects_analytics.json')
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
    message: '确定要清理项目分析数据吗？此操作不可恢复。',
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
    await api.delete('/analytics/data/old_logs')
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
