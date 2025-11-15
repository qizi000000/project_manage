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
      <!-- 项目概览统计 -->
      <div class="col-12">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">项目概览</div>
            <div class="row q-col-gutter-md">
              <div class="col-12 col-sm-6 col-md-3">
                <q-card flat class="bg-primary-1">
                  <q-card-section class="text-center">
                    <div class="text-h4 text-primary">{{ analyticsData.summary?.total_projects || 0 }}</div>
                    <div class="text-caption">总项目数</div>
                  </q-card-section>
                </q-card>
              </div>
              <div class="col-12 col-sm-6 col-md-3">
                <q-card flat class="bg-positive-1">
                  <q-card-section class="text-center">
                    <div class="text-h4 text-positive">{{ analyticsData.summary?.completed_projects || 0 }}</div>
                    <div class="text-caption">已完成</div>
                  </q-card-section>
                </q-card>
              </div>
              <div class="col-12 col-sm-6 col-md-3">
                <q-card flat class="bg-warning-1">
                  <q-card-section class="text-center">
                    <div class="text-h4 text-warning">{{ analyticsData.summary?.overdue_projects || 0 }}</div>
                    <div class="text-caption">逾期项目</div>
                  </q-card-section>
                </q-card>
              </div>
              <div class="col-12 col-sm-6 col-md-3">
                <q-card flat class="bg-info-1">
                  <q-card-section class="text-center">
                    <div class="text-h4 text-info">{{ analyticsData.summary?.active_projects || 0 }}</div>
                    <div class="text-caption">活跃项目</div>
                  </q-card-section>
                </q-card>
              </div>
            </div>
            <div class="row q-col-gutter-md q-mt-md">
              <div class="col-12 col-md-6">
                <q-card flat class="bg-secondary-1">
                  <q-card-section class="text-center">
                    <div class="text-h5 text-secondary">{{ analyticsData.summary?.completion_rate || 0 }}%</div>
                    <div class="text-caption">完成率</div>
                  </q-card-section>
                </q-card>
              </div>
              <div class="col-12 col-md-6">
                <q-card flat class="bg-accent-1">
                  <q-card-section class="text-center">
                    <div class="text-h5 text-accent">{{ analyticsData.summary?.avg_duration_days || 0 }}天</div>
                    <div class="text-caption">平均工期</div>
                  </q-card-section>
                </q-card>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

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

    <div class="row q-col-gutter-md q-mb-md">
      <!-- 项目团队分布 -->
      <div class="col-12 col-md-6">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">项目团队分布</div>
            <div class="chart-container">
              <canvas ref="teamChart"></canvas>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- 项目创建趋势 -->
      <div class="col-12 col-md-6">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">项目创建趋势</div>
            <div class="chart-container">
              <canvas ref="trendChart"></canvas>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>
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
const teamChart = ref(null)
const trendChart = ref(null)

// 加载状态
const loading = ref(false)
const exporting = ref(false)
const deleting = ref(false)

// 数据
const analyticsData = ref({
  status_distribution: [],
  owner_distribution: [],
  team_distribution: [],
  monthly_trend: [],
  summary: {
    total_projects: 0,
    completed_projects: 0,
    completion_rate: 0,
    overdue_projects: 0,
    active_projects: 0,
    avg_duration_days: 0
  }
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
  updateTeamChart()
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

function updateTeamChart() {
  if (!teamChart.value) return

  const ctx = teamChart.value.getContext('2d')
  if (window.teamChartInstance) {
    window.teamChartInstance.destroy()
  }

  window.teamChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: analyticsData.value.team_distribution.map(item => item.team),
      datasets: [{
        label: '项目数量',
        data: analyticsData.value.team_distribution.map(item => item.count),
        backgroundColor: '#9c27b0'
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
