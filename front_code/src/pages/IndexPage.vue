<template>
  <q-page class="q-pa-md">
    <!-- 页面标题 -->
    <div class="row items-center q-mb-lg">
      <div class="text-h4 q-mr-md">仪表盘</div>
      <q-space />
      <q-btn outline color="primary" icon="refresh" label="刷新" :loading="loading" @click="loadDashboardData" />
    </div>

    <!-- 统计卡片区域 -->
    <div class="row q-col-gutter-md ">
      <div class="col-12 col-sm-6 col-md-3">
        <q-card flat bordered class="stat-card">
          <q-card-section class="text-center">
            <q-icon name="folder" size="2.5rem" color="primary" class="q-mb-sm" />
            <div class="text-h5 text-weight-bold">{{ stats.projects.total }}</div>
            <div class="text-caption text-grey-7">总项目数</div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-sm-6 col-md-3">
        <q-card flat bordered class="stat-card">
          <q-card-section class="text-center">
            <q-icon name="assignment" size="2.5rem" color="blue" class="q-mb-sm" />
            <div class="text-h5 text-weight-bold">{{ stats.tasks.total }}</div>
            <div class="text-caption text-grey-7">总任务数</div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-sm-6 col-md-3">
        <q-card flat bordered class="stat-card">
          <q-card-section class="text-center">
            <q-icon name="check_circle" size="2.5rem" color="positive" class="q-mb-sm" />
            <div class="text-h5 text-weight-bold">{{ stats.tasks.completed }}</div>
            <div class="text-caption text-grey-7">已完成任务</div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-sm-6 col-md-3">
        <q-card flat bordered class="stat-card">
          <q-card-section class="text-center">
            <q-icon name="group" size="2.5rem" color="orange" class="q-mb-sm" />
            <div class="text-h5 text-weight-bold">{{ stats.users.total }}</div>
            <div class="text-caption text-grey-7">总用户数</div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <div class="row q-mt-md ">
      <div class="col-12">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-h6 q-mb-md">快速操作</div>
            <div class="row q-col-gutter-md">
              <div class="col-12 col-sm-6 col-md-3">
                <q-btn outline color="primary" icon="add" label="创建项目" class="full-width" @click="createProject" />
              </div>
              <div class="col-12 col-sm-6 col-md-3">
                <q-btn outline color="secondary" icon="assignment" label="创建任务" class="full-width"
                  @click="createTask" />
              </div>
              <div class="col-12 col-sm-6 col-md-3">
                <q-btn outline color="positive" icon="group" label="管理团队" class="full-width"
                  @click="$router.push('/teams')" />
              </div>
              <div class="col-12 col-sm-6 col-md-3">
                <q-btn outline color="info" icon="analytics" label="查看统计" class="full-width"
                  @click="$router.push('/analytics/projects')" />
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>
    <!-- 待办任务 -->
    <div class="row q-mt-md q-mb-md">
      <div class="col-12">
        <q-card flat bordered>
          <q-card-section>
            <div class="row items-center q-mb-md">
              <div class="text-h6">我的待办任务</div>
              <q-space />
              <q-btn
                flat
                dense
                color="primary"
                icon="arrow_forward"
                label="查看全部"
                @click="$router.push('/tasks')"
              />
            </div>
            <q-list separator>
              <q-item
                v-for="task in pendingTasks"
                :key="task.id"
                clickable
                @click="$router.push(`/tasks/${task.id}`)"
              >
                <q-item-section avatar>
                  <q-icon
                    :name="getTaskStatusIcon(task.status)"
                    :color="getTaskStatusColor(task.status)"
                  />
                </q-item-section>
                <q-item-section>
                  <q-item-label>{{ task.title }}</q-item-label>
                  <q-item-label caption>
                    {{ task.project_name }} • {{ task.status }}
                    <q-badge
                      v-if="task.priority"
                      :color="getPriorityColor(task.priority)"
                      :label="task.priority"
                      class="q-ml-sm"
                    />
                  </q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-item-label caption>{{ formatTime(task.created_at) }}</q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
            <div v-if="!pendingTasks.length" class="text-center text-grey-6 q-pa-md">
              <q-icon name="check_circle" size="2rem" class="q-mb-sm" />
              <div>暂无待办任务</div>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>
    <!-- 图表和活动区域 -->
    <div class="row q-col-gutter-lg">
      <!-- 任务状态分布图表 -->
      <div class="col-12 col-lg-6">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-h6 q-mb-md">任务状态分布</div>
            <div class="chart-container">
              <canvas ref="taskStatusChart"></canvas>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- 最近活动 -->
      <div class="col-12 col-lg-6">
        <q-card flat bordered class="activity-card">
          <q-card-section>
            <div class="text-h6 q-mb-md">最近活动</div>
            <div class="activity-container">
              <q-list separator>
                <q-item v-for="activity in recentActivities" :key="activity.timestamp">
                  <q-item-section avatar>
                    <q-icon :name="getActivityIcon(activity.type)" :color="getActivityColor(activity.type)" size="sm" />
                  </q-item-section>
                  <q-item-section>
                    <q-item-label class="text-body2">{{ activity.title }}</q-item-label>
                    <q-item-label caption>
                      {{ activity.user }} • {{ formatTime(activity.timestamp) }}
                    </q-item-label>
                  </q-item-section>
                </q-item>
              </q-list>
              <div v-if="!recentActivities.length" class="text-center text-grey-6 q-pa-md">
                <q-icon name="info" size="2rem" class="q-mb-sm" />
                <div>暂无活动记录</div>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>



    <!-- 快速操作 -->

  </q-page>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { api } from 'boot/axios'
import { date } from 'quasar'
import { useRouter } from 'vue-router'
import Chart from 'chart.js/auto'

// 数据
const router = useRouter()
const loading = ref(false)
const stats = reactive({
  projects: { total: 0 },
  tasks: { total: 0, completed: 0, in_progress: 0, pending: 0 },
  users: { total: 0 },
  teams: { total: 0 }
})
const recentActivities = ref([])
const pendingTasks = ref([])
const taskStatusChart = ref(null)

// 方法
async function loadDashboardData() {
  loading.value = true
  try {
    // 并行加载所有数据
    const [statsRes, activitiesRes, tasksRes] = await Promise.all([
      api.get('/dashboard/stats'),
      api.get('/dashboard/recent-activity'),
      api.get('/dashboard/pending-tasks')
    ])

    // 更新统计数据
    Object.assign(stats, statsRes.data)

    // 更新活动数据
    recentActivities.value = activitiesRes.data

    // 更新待办任务
    pendingTasks.value = tasksRes.data

    // 更新图表
    updateTaskStatusChart()
  } catch (error) {
    console.error('加载仪表盘数据失败:', error)
  } finally {
    loading.value = false
  }
}

function updateTaskStatusChart() {
  if (!taskStatusChart.value) return

  const ctx = taskStatusChart.value.getContext('2d')

  // 销毁现有图表
  if (window.taskChart) {
    window.taskChart.destroy()
  }

  window.taskChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['待处理', '进行中', '已完成'],
      datasets: [{
        data: [
          stats.tasks.pending,
          stats.tasks.in_progress,
          stats.tasks.completed
        ],
        backgroundColor: [
          '#f44336', // 红色 - 待处理
          '#ff9800', // 橙色 - 进行中
          '#4caf50'  // 绿色 - 已完成
        ],
        borderWidth: 2
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

function getActivityIcon(type) {
  const icons = {
    project_created: 'folder',
    task_created: 'assignment',
    task_updated: 'edit'
  }
  return icons[type] || 'info'
}

function getActivityColor(type) {
  const colors = {
    project_created: 'primary',
    task_created: 'secondary',
    task_updated: 'info'
  }
  return colors[type] || 'grey'
}

function getTaskStatusIcon(status) {
  const icons = {
    '待处理': 'schedule',
    '进行中': 'play_arrow',
    '已完成': 'check_circle',
    '已取消': 'cancel'
  }
  return icons[status] || 'help'
}

function getTaskStatusColor(status) {
  const colors = {
    '待处理': 'negative',
    '进行中': 'warning',
    '已完成': 'positive',
    '已取消': 'grey'
  }
  return colors[status] || 'grey'
}

function getPriorityColor(priority) {
  const colors = {
    '低': 'grey',
    '中': 'blue',
    '高': 'orange',
    '紧急': 'red'
  }
  return colors[priority] || 'grey'
}

function formatTime(timestamp) {
  return date.formatDate(new Date(timestamp), 'MM/DD HH:mm')
}

function createProject() {
  // 跳转到项目列表页面并传递参数打开新建项目弹窗
  router.push({ name: 'projects-list', query: { create: 'true' } })
}

function createTask() {
  // 跳转到任务列表页面并传递参数打开新建任务弹窗
  router.push({ name: 'tasks-list', query: { create: 'true' } })
}

// 生命周期
onMounted(() => {
  loadDashboardData()
})
</script>

<style scoped>
.stat-card {
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.chart-container {
  height: 240px;
  position: relative;
}

.activity-container {
  height: 240px;
  overflow-y: auto;
}
</style>
