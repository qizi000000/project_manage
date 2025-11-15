<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="text-h6">用户统计</div>
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
      <!-- 用户概览统计 -->
      <div class="col-12">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">用户概览</div>
            <div class="row q-col-gutter-md">
              <div class="col-12 col-sm-6 col-md-3">
                <q-card flat class="bg-primary-1">
                  <q-card-section class="text-center">
                    <div class="text-h4 text-primary">{{ analyticsData.total_users || 0 }}</div>
                    <div class="text-caption">总用户数</div>
                  </q-card-section>
                </q-card>
              </div>
              <div class="col-12 col-sm-6 col-md-3">
                <q-card flat class="bg-info-1">
                  <q-card-section class="text-center">
                    <div class="text-h4 text-info">{{ analyticsData.active_users || 0 }}</div>
                    <div class="text-caption">活跃用户</div>
                  </q-card-section>
                </q-card>
              </div>
              <div class="col-12 col-sm-6 col-md-3">
                <q-card flat class="bg-secondary-1">
                  <q-card-section class="text-center">
                    <div class="text-h4 text-secondary">{{ analyticsData.activity_rate || 0 }}%</div>
                    <div class="text-caption">活跃率</div>
                  </q-card-section>
                </q-card>
              </div>
              <div class="col-12 col-sm-6 col-md-3">
                <q-card flat class="bg-accent-1">
                  <q-card-section class="text-center">
                    <div class="text-h4 text-accent">{{ analyticsData.role_distribution?.length || 0 }}</div>
                    <div class="text-caption">角色类型</div>
                  </q-card-section>
                </q-card>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- 用户角色分布 -->
      <div class="col-12 col-md-6">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">用户角色分布</div>
            <div class="chart-container">
              <canvas ref="roleChart"></canvas>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- 用户注册趋势 -->
      <div class="col-12 col-md-6">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">用户注册趋势</div>
            <div class="chart-container">
              <canvas ref="registrationChart"></canvas>
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
const roleChart = ref(null)
const registrationChart = ref(null)

// 加载状态
const loading = ref(false)
const exporting = ref(false)
const deleting = ref(false)

// 数据
const analyticsData = ref({
  role_distribution: [],
  monthly_registration_trend: [],
  active_users: 0,
  total_users: 0,
  activity_rate: 0
})

// 权限检查
const hasExportPermission = computed(() => authStore.hasPermission('analytics.export'))
const hasDeletePermission = computed(() => authStore.hasPermission('analytics.delete'))

// 加载数据
async function loadAnalyticsData() {
  loading.value = true
  try {
    const response = await api.get('/analytics/users')
    analyticsData.value = response.data
    updateCharts()
  } catch (error) {
    console.error('加载用户分析数据失败:', error)
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
  updateRoleChart()
  updateRegistrationChart()
}

function updateRoleChart() {
  if (!roleChart.value) return

  const ctx = roleChart.value.getContext('2d')
  if (window.userRoleChartInstance) {
    window.userRoleChartInstance.destroy()
  }

  window.userRoleChartInstance = new Chart(ctx, {
    type: 'pie',
    data: {
      labels: analyticsData.value.role_distribution.map(item => item.role),
      datasets: [{
        data: analyticsData.value.role_distribution.map(item => item.count),
        backgroundColor: [
          '#4caf50', // 管理员
          '#2196f3', // 普通用户
          '#ff9800', // 项目经理
          '#9c27b0', // 开发者
          '#f44336'  // 其他
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

function updateRegistrationChart() {
  if (!registrationChart.value) return

  const ctx = registrationChart.value.getContext('2d')
  if (window.userRegistrationChartInstance) {
    window.userRegistrationChartInstance.destroy()
  }

  window.userRegistrationChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: analyticsData.value.monthly_registration_trend.map(item => `${item.month}月`),
      datasets: [{
        label: '注册用户数量',
        data: analyticsData.value.monthly_registration_trend.map(item => item.count),
        borderColor: '#2196f3',
        backgroundColor: 'rgba(33, 150, 243, 0.1)',
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
    const response = await api.get('/analytics/export/users', {
      responseType: 'blob'
    })

    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'users_analytics.json')
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
    message: '确定要清理用户分析数据吗？此操作不可恢复。',
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
