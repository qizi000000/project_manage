<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="text-h6">团队统计</div>
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
      <!-- 团队概览统计 -->
      <div class="col-12">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">团队概览</div>
            <div class="row q-col-gutter-md">
              <div class="col-12 col-sm-6 col-md-3">
                <q-card flat class="bg-primary-1">
                  <q-card-section class="text-center">
                    <div class="text-h4 text-primary">{{ analyticsData.summary?.total_teams || 0 }}</div>
                    <div class="text-caption">总团队数</div>
                  </q-card-section>
                </q-card>
              </div>
              <div class="col-12 col-sm-6 col-md-3">
                <q-card flat class="bg-info-1">
                  <q-card-section class="text-center">
                    <div class="text-h4 text-info">{{ analyticsData.summary?.total_members || 0 }}</div>
                    <div class="text-caption">总成员数</div>
                  </q-card-section>
                </q-card>
              </div>
              <div class="col-12 col-sm-6 col-md-3">
                <q-card flat class="bg-secondary-1">
                  <q-card-section class="text-center">
                    <div class="text-h4 text-secondary">{{ analyticsData.summary?.avg_members_per_team || 0 }}</div>
                    <div class="text-caption">平均团队规模</div>
                  </q-card-section>
                </q-card>
              </div>
              <div class="col-12 col-sm-6 col-md-3">
                <q-card flat class="bg-accent-1">
                  <q-card-section class="text-center">
                    <div class="text-h4 text-accent">{{ analyticsData.summary?.total_projects || 0 }}</div>
                    <div class="text-caption">总项目数</div>
                  </q-card-section>
                </q-card>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- 团队成员分布 -->
      <div class="col-12 col-md-6">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">团队成员分布</div>
            <div class="chart-container">
              <canvas ref="membersChart"></canvas>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- 团队项目分布 -->
      <div class="col-12 col-md-6">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">团队项目分布</div>
            <div class="chart-container">
              <canvas ref="projectsChart"></canvas>
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
const membersChart = ref(null)
const projectsChart = ref(null)

// 加载状态
const loading = ref(false)
const exporting = ref(false)
const deleting = ref(false)

// 数据
const analyticsData = ref({
  team_members_distribution: [],
  team_projects_distribution: [],
  summary: {
    total_teams: 0,
    total_members: 0,
    avg_members_per_team: 0,
    total_projects: 0
  }
})

// 权限检查
const hasExportPermission = computed(() => authStore.hasPermission('analytics.export'))
const hasDeletePermission = computed(() => authStore.hasPermission('analytics.delete'))

// 加载数据
async function loadAnalyticsData() {
  loading.value = true
  try {
    const response = await api.get('/analytics/teams')
    analyticsData.value = response.data

    // 计算汇总数据
    const totalTeams = analyticsData.value.team_members_distribution.length
    const totalMembers = analyticsData.value.team_members_distribution.reduce((sum, item) => sum + item.member_count, 0)
    const totalProjects = analyticsData.value.team_projects_distribution.reduce((sum, item) => sum + item.project_count, 0)
    const avgMembers = totalTeams > 0 ? Math.round(totalMembers / totalTeams * 10) / 10 : 0

    analyticsData.value.summary = {
      total_teams: totalTeams,
      total_members: totalMembers,
      avg_members_per_team: avgMembers,
      total_projects: totalProjects
    }

    updateCharts()
  } catch (error) {
    console.error('加载团队分析数据失败:', error)
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
  updateMembersChart()
  updateProjectsChart()
}

function updateMembersChart() {
  if (!membersChart.value) return

  const ctx = membersChart.value.getContext('2d')
  if (window.teamMembersChartInstance) {
    window.teamMembersChartInstance.destroy()
  }

  window.teamMembersChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: analyticsData.value.team_members_distribution.map(item => item.team),
      datasets: [{
        label: '成员数量',
        data: analyticsData.value.team_members_distribution.map(item => item.member_count),
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

function updateProjectsChart() {
  if (!projectsChart.value) return

  const ctx = projectsChart.value.getContext('2d')
  if (window.teamProjectsChartInstance) {
    window.teamProjectsChartInstance.destroy()
  }

  window.teamProjectsChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: analyticsData.value.team_projects_distribution.map(item => item.team),
      datasets: [{
        label: '项目数量',
        data: analyticsData.value.team_projects_distribution.map(item => item.project_count),
        backgroundColor: '#4caf50'
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
    const response = await api.get('/analytics/export/teams', {
      responseType: 'blob'
    })

    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'teams_analytics.json')
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
    message: '确定要清理团队分析数据吗？此操作不可恢复。',
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
