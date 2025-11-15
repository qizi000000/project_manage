<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="text-h6">角色统计</div>
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
      <!-- 角色概览统计 -->
      <div class="col-12">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">角色概览</div>
            <div class="row q-col-gutter-md">
              <div class="col-12 col-sm-6 col-md-3">
                <q-card flat class="bg-primary-1">
                  <q-card-section class="text-center">
                    <div class="text-h4 text-primary">{{ analyticsData.summary?.total_roles || 0 }}</div>
                    <div class="text-caption">总角色数</div>
                  </q-card-section>
                </q-card>
              </div>
              <div class="col-12 col-sm-6 col-md-3">
                <q-card flat class="bg-info-1">
                  <q-card-section class="text-center">
                    <div class="text-h4 text-info">{{ analyticsData.summary?.total_users || 0 }}</div>
                    <div class="text-caption">总用户数</div>
                  </q-card-section>
                </q-card>
              </div>
              <div class="col-12 col-sm-6 col-md-3">
                <q-card flat class="bg-secondary-1">
                  <q-card-section class="text-center">
                    <div class="text-h4 text-secondary">{{ analyticsData.summary?.avg_users_per_role || 0 }}</div>
                    <div class="text-caption">平均角色用户数</div>
                  </q-card-section>
                </q-card>
              </div>
              <div class="col-12 col-sm-6 col-md-3">
                <q-card flat class="bg-accent-1">
                  <q-card-section class="text-center">
                    <div class="text-h4 text-accent">{{ analyticsData.summary?.total_permissions || 0 }}</div>
                    <div class="text-caption">总权限数</div>
                  </q-card-section>
                </q-card>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- 角色权限分布 -->
      <div class="col-12 col-md-6">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">角色权限分布</div>
            <div class="chart-container">
              <canvas ref="permissionsChart"></canvas>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- 角色用户分布 -->
      <div class="col-12 col-md-6">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">角色用户分布</div>
            <div class="chart-container">
              <canvas ref="usersChart"></canvas>
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
const permissionsChart = ref(null)
const usersChart = ref(null)

// 加载状态
const loading = ref(false)
const exporting = ref(false)
const deleting = ref(false)

// 数据
const analyticsData = ref({
  role_permissions_distribution: [],
  role_users_distribution: [],
  summary: {
    total_roles: 0,
    total_users: 0,
    avg_users_per_role: 0,
    total_permissions: 0
  }
})

// 权限检查
const hasExportPermission = computed(() => authStore.hasPermission('analytics.export'))
const hasDeletePermission = computed(() => authStore.hasPermission('analytics.delete'))

// 加载数据
async function loadAnalyticsData() {
  loading.value = true
  try {
    const response = await api.get('/analytics/roles')
    analyticsData.value = response.data

    // 计算汇总数据
    const totalRoles = analyticsData.value.role_permissions_distribution.length
    const totalUsers = analyticsData.value.role_users_distribution.reduce((sum, item) => sum + item.user_count, 0)
    const totalPermissions = analyticsData.value.role_permissions_distribution.reduce((sum, item) => sum + item.permission_count, 0)
    const avgUsers = totalRoles > 0 ? Math.round(totalUsers / totalRoles * 10) / 10 : 0

    analyticsData.value.summary = {
      total_roles: totalRoles,
      total_users: totalUsers,
      avg_users_per_role: avgUsers,
      total_permissions: totalPermissions
    }

    updateCharts()
  } catch (error) {
    console.error('加载角色分析数据失败:', error)
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
  updatePermissionsChart()
  updateUsersChart()
}

function updatePermissionsChart() {
  if (!permissionsChart.value) return

  const ctx = permissionsChart.value.getContext('2d')
  if (window.rolePermissionsChartInstance) {
    window.rolePermissionsChartInstance.destroy()
  }

  window.rolePermissionsChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: analyticsData.value.role_permissions_distribution.map(item => item.role),
      datasets: [{
        label: '权限数量',
        data: analyticsData.value.role_permissions_distribution.map(item => item.permission_count),
        backgroundColor: '#ff9800'
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

function updateUsersChart() {
  if (!usersChart.value) return

  const ctx = usersChart.value.getContext('2d')
  if (window.roleUsersChartInstance) {
    window.roleUsersChartInstance.destroy()
  }

  window.roleUsersChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: analyticsData.value.role_users_distribution.map(item => item.role),
      datasets: [{
        label: '用户数量',
        data: analyticsData.value.role_users_distribution.map(item => item.user_count),
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

// 导出数据
async function exportData() {
  exporting.value = true
  try {
    const response = await api.get('/analytics/export/roles', {
      responseType: 'blob'
    })

    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'roles_analytics.json')
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
    message: '确定要清理角色分析数据吗？此操作不可恢复。',
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
    await api.delete('/analytics/data/cache')
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
