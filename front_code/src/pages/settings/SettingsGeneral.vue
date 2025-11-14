<template>
  <q-page class="q-pa-md">
    <!-- 页面标题 -->
    <div class="row items-center q-mb-lg">
      <div class="text-h4 q-mr-md">常规设置</div>
    </div>
   

    <div class="">
      <div class="row q-col-gutter-md">
        <!-- 左侧：账号信息 -->
        <div class="col-12 col-md-8 ">
          <!-- 账号信息 -->
          <q-card class="settings-card" flat bordered>
            <q-card-section class="card-header">
              <div class="row items-center">
                <div class="col">
                  <div class="text-h6 text-weight-medium">账号信息</div>
                  <div class="text-caption text-grey-7">管理您的个人资料和账号设置</div>
                </div>
                <q-btn flat round icon="edit" color="primary" @click="showProfileDialog = true" size="sm">
                  <q-tooltip>编辑资料</q-tooltip>
                </q-btn>
              </div>
            </q-card-section>
            <q-separator />
            <q-card-section class="card-content">
              <div class="account-card-grid">
                <div class="account-card-left">
                  <q-avatar size="96px" class="profile-avatar">
                    <img :src="me?.avatar || defaultAvatar" alt="avatar" />
                  </q-avatar>
                  <div class="profile-name text-h6 text-weight-bold q-mt-md">
                    {{ me?.nickname || me?.username }}
                  </div>
                  <div class="profile-username text-caption text-grey-7">@{{ me?.username }}</div>
                  <q-chip v-if="me?.is_admin" color="positive" text-color="white" size="sm" dense
                    class="q-mt-sm">
                    管理员
                  </q-chip>
                  <div class="profile-role text-caption text-grey-7 q-mt-xs">{{ me?.role_name || '普通用户' }}</div>
                </div>
                <div class="account-card-right">
                  <div class="account-info-row">
                    <span class="info-label">邮箱</span>
                    <span class="info-value">{{ me?.email || '未设置' }}</span>
                  </div>
                  <div class="account-info-row">
                    <span class="info-label">电话</span>
                    <span class="info-value">{{ me?.phone || '未设置' }}</span>
                  </div>
                  <div class="account-info-row">
                    <span class="info-label">微信</span>
                    <span class="info-value">{{ me?.wechat || '未设置' }}</span>
                  </div>
                  <div class="account-info-row">
                    <span class="info-label">个性签名</span>
                    <div class="remark-container">
                      <span class="info-value">{{ displayRemark }}</span>
                      <q-btn
                        v-if="showExpandButton"
                        flat
                        dense
                        size="sm"
                        color="primary"
                        :label="remarkExpanded ? '收起' : '展开'"
                        @click="toggleRemarkExpansion"
                        class="expand-btn"
                      />
                    </div>
                  </div>
                    <div class="account-info-row" style="display: flex; flex-direction: row; justify-content: space-between; align-items: center;">
                      <span class="info-label">注册时间</span>
                      <span class="info-value">{{ formatDate(me?.created_at) }}</span>
                      <span class="info-label">最后登录</span>
                      <span class="info-value">{{ formatDate(me?.last_login) || '首次登录' }}</span>
                    </div>
                </div>
              </div>
            </q-card-section>
          </q-card>

          <!-- 登录日志 -->
          <q-card class="settings-card" flat bordered>
            <q-card-section class="card-header">
              <div class="row items-center">
                <div class="col">
                  <div class="text-h6 text-weight-medium">登录日志</div>
                  <div class="text-caption text-grey-7">最近的登录记录</div>
                </div>
                <q-icon name="history" size="24px" color="grey" />
              </div>
            </q-card-section>

            <q-separator />

              <q-card-section class="card-content">
                <div v-if="loginLogs.length === 0" class="text-center text-grey-6 q-pa-md">
                  <q-icon name="info" size="48px" class="q-mb-sm" />
                  <div>暂无登录记录</div>
                </div>

                <div v-else class="login-logs">
                  <q-list separator bordered class="no-padding">
                    <q-item v-for="log in loginLogs" :key="log.id" class="login-log-item">
                      <q-item-section avatar style="min-width:56px;">
                        <q-icon :name="log.user_agent ? 'devices' : 'history'" color="primary" size="24px" />
                      </q-item-section>

                      <q-item-section>
                        <q-item-label class="text-body2">{{ formatDateTime(log.created_at) }}</q-item-label>
                        <q-item-label caption class="text-caption">
                          IP: {{ log.ip_address }}
                          <span class="q-ml-sm">•</span>
                          <span class="q-ml-sm">{{ getDeviceLabel(log.user_agent) }} {{ getBrowserLabel(log.user_agent) }}</span>
                        </q-item-label>
                      </q-item-section>

                      <q-item-section side top style="min-width: 120px; text-align: right;">
                        <q-btn flat dense color="primary" label="查看" @click.stop="viewLogDetail(log)" />
                      </q-item-section>
                    </q-item>
                  </q-list>
                </div>
              </q-card-section>
          </q-card>
        </div>

        <!-- 右侧：安全设置和偏好设置 -->
        <div class="col-12 col-md-4 ">
          <!-- 安全设置 -->
          <q-card class="settings-card" flat bordered>
            <q-card-section class="card-header">
              <div class="row items-center">
                <div class="col">
                  <div class="text-h6 text-weight-medium">安全设置</div>
                  <div class="text-caption text-grey-7">保护您的账号安全</div>
                </div>
                <q-icon name="security" size="24px" color="primary" />
              </div>
            </q-card-section>

            <q-separator />

            <q-card-section class="card-content">
              <q-btn color="primary" label="修改密码" icon="lock" unelevated rounded @click="showPasswordDialog = true"
                class="full-width" />
              <div class="text-caption text-grey-7 q-mt-sm">
                定期修改密码可以提高账号安全性
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- 修改密码对话框 -->
      <q-dialog v-model="showPasswordDialog" persistent>
        <q-card style="min-width: 400px">
          <q-card-section class="row items-center">
            <div class="text-h6">修改密码</div>
            <q-space />
            <q-btn flat round dense icon="close" @click="closePasswordDialog" />
          </q-card-section>
          <q-separator />
          <q-card-section>
            <q-form @submit="changePassword" class="q-gutter-md">
              <q-input v-model="passwordForm.oldPassword" label="当前密码" outlined dense type="password"
                :rules="[v => !!v || '请输入当前密码']" autofocus />

              <q-input v-model="passwordForm.newPassword" label="新密码" outlined dense type="password" :rules="[
                v => !!v || '请输入新密码',
                v => v.length >= 6 || '密码至少6个字符'
              ]" />

              <q-input v-model="passwordForm.confirmPassword" label="确认新密码" outlined dense type="password" :rules="[
                v => !!v || '请确认新密码',
                v => v === passwordForm.newPassword || '两次输入的密码不一致'
              ]" />

              <div class="q-mt-md text-caption text-grey-7">
                <q-icon name="info" size="sm" />
                密码强度要求：至少6个字符，建议包含字母和数字
              </div>
            </q-form>
          </q-card-section>

          <q-card-actions align="right">
            <q-btn flat label="取消" color="grey" @click="closePasswordDialog" />
            <q-btn type="submit" color="primary" label="确认修改" :loading="passwordLoading" @click="changePassword" />
          </q-card-actions>
        </q-card>
      </q-dialog>

      <!-- 编辑资料对话框 -->
      <q-dialog v-model="showProfileDialog" persistent>
        <q-card style="min-width: 480px; max-width: 520px; border-radius: 16px;">
          <q-card-section class="q-pa-none">
            <div class="profile-edit-header flex flex-center column q-pa-xl">
              <div class="avatar-container">
                <q-avatar size="96px" class="profile-avatar">
                  <img :src="me?.avatar || defaultAvatar" alt="avatar" />
                </q-avatar>
                <q-btn
                  fab
                  mini
                  color="primary"
                  icon="camera_alt"
                  class="avatar-edit-btn"
                  @click="triggerAvatarUpload"
                >
                  <q-tooltip>更换头像</q-tooltip>
                </q-btn>
              </div>
              <input
                ref="avatarInput"
                type="file"
                accept="image/*"
                style="display: none"
                @change="handleAvatarChange"
              />
              <div class="text-h6 text-weight-bold q-mt-md">{{ me?.nickname || me?.username }}</div>
              <div class="text-caption text-grey-7">{{ me?.role_name || '普通用户' }}</div>
            </div>
          </q-card-section>
          <q-separator />
          <q-card-section class="q-pa-lg">
            <q-form @submit="updateProfile" class="profile-form">
              <div class="form-group q-mb-md">
                <q-input
                  v-model="profileForm.nickname"
                  label="昵称"
                  outlined
                  dense
                  prepend-inner-icon="person"
                  :rules="[v => !v || v.length <= 50 || '昵称不能超过50个字符']"
                  placeholder="请输入昵称"
                  class="form-input"
                />
              </div>
              <div class="form-group q-mb-md">
                <q-input
                  v-model="profileForm.email"
                  label="邮箱地址"
                  outlined
                  dense
                  type="email"
                  prepend-inner-icon="email"
                  :rules="[
                    v => !v || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) || '请输入有效的邮箱地址'
                  ]"
                  placeholder="请输入邮箱地址"
                  class="form-input"
                />
              </div>
              <div class="form-group q-mb-md">
                <q-input
                  v-model="profileForm.phone"
                  label="手机号码"
                  outlined
                  dense
                  prepend-inner-icon="phone"
                  :rules="[
                    v => !v || /^1[3-9]\d{9}$/.test(v) || '请输入有效的手机号码'
                  ]"
                  placeholder="请输入手机号码"
                  class="form-input"
                />
              </div>
              <div class="form-group q-mb-md">
                <q-input
                  v-model="profileForm.wechat"
                  label="微信号"
                  outlined
                  dense
                  prepend-inner-icon="chat"
                  :rules="[v => !v || v.length <= 50 || '微信号不能超过50个字符']"
                  placeholder="请输入微信号"
                  class="form-input"
                />
              </div>
              <div class="form-group">
                <q-input
                  v-model="profileForm.remark"
                  label="个性签名"
                  outlined
                  dense
                  type="textarea"
                  rows="3"
                  prepend-inner-icon="edit"
                  :rules="[v => !v || v.length <= 200 || '个性签名不能超过200个字符']"
                  placeholder="写下您的个性签名..."
                  class="form-input"
                />
              </div>
            </q-form>
          </q-card-section>
          <q-separator />
          <q-card-actions class="q-pa-md">
            <q-space />
            <q-btn flat label="取消" color="grey-7" @click="closeProfileDialog" class="action-btn" />
            <q-btn type="submit" color="primary" label="保存修改" :loading="profileLoading" :disable="!profileChanged"
              @click="updateProfile" class="action-btn" unelevated rounded />
          </q-card-actions>
        </q-card>
      </q-dialog>

      <!-- 登录日志详情对话框 -->
      <q-dialog v-model="showLogDetailDialog" persistent>
        <q-card style="min-width: 500px; max-width: 600px;">
          <q-card-section class="row items-center">
            <div class="text-h6">登录详情</div>
            <q-space />
            <q-btn flat round dense icon="close" @click="closeLogDetailDialog" />
          </q-card-section>
          <q-separator />
          <q-card-section v-if="selectedLog" class="q-gutter-md">
            <div class="row">
              <div class="col-12">
                <q-icon name="access_time" color="primary" class="q-mr-sm" />
                <strong>登录时间：</strong>{{ formatDateTime(selectedLog.created_at) }}
              </div>
            </div>
            <div class="row">
              <div class="col-12">
                <q-icon name="location_on" color="orange" class="q-mr-sm" />
                <strong>IP 地址：</strong>{{ selectedLog.ip_address }}
              </div>
            </div>
            <div class="row">
              <div class="col-12">
                <q-icon name="devices" color="teal" class="q-mr-sm" />
                <strong>设备类型：</strong>{{ getDeviceLabel(selectedLog.user_agent) }}
              </div>
            </div>
            <div class="row">
              <div class="col-12">
                <q-icon name="web" color="purple" class="q-mr-sm" />
                <strong>浏览器：</strong>{{ getBrowserLabel(selectedLog.user_agent) }}
              </div>
            </div>
            <div class="row">
              <div class="col-12">
                <q-icon name="info" color="grey" class="q-mr-sm" />
                <strong>User Agent：</strong>
                <div class="q-mt-sm q-pa-sm bg-grey-1 rounded-borders text-caption" style="word-break: break-all;">
                  {{ selectedLog.user_agent || '无' }}
                </div>
              </div>
            </div>
          </q-card-section>
          <q-card-actions align="right">
            <q-btn flat label="关闭" color="grey" @click="closeLogDetailDialog" />
          </q-card-actions>
        </q-card>
      </q-dialog>
    </div>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { api } from 'boot/axios'

const $q = useQuasar()

// 用户信息
const me = ref(null)

// 登录日志
const loginLogs = ref([])

// 登录日志详情对话框
const showLogDetailDialog = ref(false)
const selectedLog = ref(null)

// 个性签名展开状态
const remarkExpanded = ref(false)

// 资料表单数据
const profileForm = ref({
  nickname: '',
  email: '',
  phone: '',
  wechat: '',
  remark: ''
})

// 头像相关
const avatarInput = ref(null)
const avatarFile = ref(null)

// 密码表单数据
const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 加载状态
const profileLoading = ref(false)
const passwordLoading = ref(false)

// 对话框状态
const showPasswordDialog = ref(false)
const showProfileDialog = ref(false)

// 计算属性
const profileChanged = computed(() => {
  return profileForm.value.nickname !== me.value?.nickname ||
    profileForm.value.email !== me.value?.email ||
    profileForm.value.phone !== me.value?.phone ||
    profileForm.value.wechat !== me.value?.wechat ||
    profileForm.value.remark !== me.value?.remark
})

const defaultAvatar = computed(() => {
  // 生成基于用户名的默认头像
  const name = me.value?.nickname || me.value?.username || 'U'
  return `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=667eea&color=fff&size=80`
})

// 个性签名显示逻辑
const displayRemark = computed(() => {
  const remark = me.value?.remark || '这个人很懒，什么都没有留下'
  if (remarkExpanded.value || remark.length <= 30) {
    return remark
  }
  return remark.substring(0, 30) + '...'
})

// 是否需要展开按钮
const showExpandButton = computed(() => {
  const remark = me.value?.remark || '这个人很懒，什么都没有留下'
  return remark.length > 30
})

// 获取用户信息
async function fetchUserInfo() {
  try {
    const { data } = await api.get('/auth/me')
    me.value = data
    // 初始化表单
    profileForm.value = {
      nickname: data.nickname || '',
      email: data.email || '',
      phone: data.phone || '',
      wechat: data.wechat || '',
      remark: data.remark || ''
    }

    // 获取登录日志
    await fetchLoginLogs()
  } catch (error) {
    console.error('获取用户信息失败:', error)
    $q.notify({
      type: 'negative',
      message: '获取用户信息失败',
      position: 'top'
    })
  }
}

// 更新用户信息
async function updateProfile() {
  profileLoading.value = true
  try {
    const { data } = await api.put('/auth/me', {
      nickname: profileForm.value.nickname || null,
      email: profileForm.value.email || null,
      phone: profileForm.value.phone || null,
      wechat: profileForm.value.wechat || null,
      remark: profileForm.value.remark || null
    })
    me.value = data
    showProfileDialog.value = false
    $q.notify({
      type: 'positive',
      message: '个人资料更新成功',
      position: 'top'
    })
  } catch (error) {
    console.error('更新用户信息失败:', error)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || '更新失败',
      position: 'top'
    })
  } finally {
    profileLoading.value = false
  }
}

// 获取登录日志
async function fetchLoginLogs() {
  try {
    const { data } = await api.get('/auth/login-logs')
    loginLogs.value = data
  } catch (error) {
    console.error('获取登录日志失败:', error)
    // 不显示错误通知，因为这不是关键功能
  }
}

// 触发头像上传
function triggerAvatarUpload() {
  avatarInput.value?.click()
}

// 处理头像文件选择
function handleAvatarChange(event) {
  const file = event.target.files[0]
  if (file) {
    // 验证文件类型
    if (!file.type.startsWith('image/')) {
      $q.notify({
        type: 'negative',
        message: '请选择图片文件',
        position: 'top'
      })
      return
    }

    // 验证文件大小 (5MB)
    if (file.size > 5 * 1024 * 1024) {
      $q.notify({
        type: 'negative',
        message: '图片大小不能超过5MB',
        position: 'top'
      })
      return
    }

    avatarFile.value = file

    // 预览头像
    const reader = new FileReader()
    reader.onload = () => {
      // 这里可以设置预览，但暂时不实现上传功能
      $q.notify({
        type: 'info',
        message: '头像上传功能开发中',
        position: 'top'
      })
    }
    reader.readAsDataURL(file)
  }
}

// 修改密码
async function changePassword() {
  passwordLoading.value = true
  try {
    await api.put('/auth/password', {
      old_password: passwordForm.value.oldPassword,
      new_password: passwordForm.value.newPassword
    })
    // 清空表单并关闭对话框
    closePasswordDialog()
    $q.notify({
      type: 'positive',
      message: '密码修改成功，请重新登录',
      position: 'top'
    })
    // 清除token并跳转到登录页
    setTimeout(() => {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }, 2000)
  } catch (error) {
    console.error('修改密码失败:', error)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || '修改失败',
      position: 'top'
    })
  } finally {
    passwordLoading.value = false
  }
}



// 关闭密码对话框
function closePasswordDialog() {
  showPasswordDialog.value = false
  passwordForm.value = {
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  }
}

// 关闭资料编辑对话框
function closeProfileDialog() {
  showProfileDialog.value = false
  // 重新初始化表单数据
  if (me.value) {
    profileForm.value = {
      nickname: me.value.nickname || '',
      email: me.value.email || '',
      phone: me.value.phone || '',
      wechat: me.value.wechat || '',
      remark: me.value.remark || ''
    }
  }
}

// 查看登录日志详情
function viewLogDetail(log) {
  selectedLog.value = log
  showLogDetailDialog.value = true
}

// 关闭登录日志详情对话框
function closeLogDetailDialog() {
  showLogDetailDialog.value = false
  selectedLog.value = null
}

// 切换个性签名展开状态
function toggleRemarkExpansion() {
  remarkExpanded.value = !remarkExpanded.value
}

// 监听明暗模式变化 - 移除，因为主题色现在由独立组件管理

// 初始化
onMounted(() => {
  fetchUserInfo()
})

function formatDate(dateString) {
  if (!dateString) return '从未'
  return new Date(dateString).toLocaleString('zh-CN')
}

function formatDateTime(dateString) {
  if (!dateString) return ''
  return new Date(dateString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 需要暴露到模板
defineExpose({
  formatDate,
  formatDateTime
})

// 解析设备类型
function getDeviceLabel(userAgent) {
  if (!userAgent) return '未知设备'
  
  const ua = userAgent.toLowerCase()
  
  if (ua.includes('mobile') || ua.includes('android') || ua.includes('iphone')) {
    return '移动设备'
  } else if (ua.includes('tablet') || ua.includes('ipad')) {
    return '平板设备'
  } else {
    return '桌面设备'
  }
}

// 解析浏览器类型
function getBrowserLabel(userAgent) {
  if (!userAgent) return '未知浏览器'
  
  const ua = userAgent.toLowerCase()
  
  if (ua.includes('chrome') && !ua.includes('edg')) {
    return 'Chrome'
  } else if (ua.includes('firefox')) {
    return 'Firefox'
  } else if (ua.includes('safari') && !ua.includes('chrome')) {
    return 'Safari'
  } else if (ua.includes('edg')) {
    return 'Edge'
  } else if (ua.includes('opera')) {
    return 'Opera'
  } else {
    return '其他浏览器'
  }
}
</script>

<style scoped>

.settings-card {
  margin-bottom: 1.25rem;
  overflow: hidden;
  background: var(--q-card-background);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.settings-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.10);
}

.card-header {
  background: transparent;
  border-bottom: 1px solid var(--q-separator-color);
}

.card-content {
  padding: 1.5rem;
}

.account-card-grid {
  display: flex;
  flex-direction: row;
  gap: 2rem;
  align-items: flex-start;
}
.account-card-left {
  min-width: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  gap: 0.5rem;
}
.account-card-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}
.account-info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.65rem 1rem;
  background: var(--q-card-background, transparent);
  border-radius: 8px;
  border: 1px solid var(--q-separator-color, rgba(0,0,0,0.04));
  margin-bottom: 0.5rem;
}
.info-label {
  font-size: 0.95rem;
  color: var(--q-text-color, #5a6a7a);
  font-weight: 500;
}
.info-value {
  font-size: 0.95rem;
  color: var(--q-text-color, #2d3a4a);
  font-weight: 600;
  text-align: right;
}
.remark-container {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex: 1;
}
.expand-btn {
  font-size: 0.8rem;
  padding: 2px 8px;
  min-height: auto;
}
@media (max-width: 900px) {
  .account-card-grid {
    flex-direction: column;
    gap: 1.2rem;
  }
  .account-card-left {
    flex-direction: row;
    justify-content: flex-start;
    min-width: 0;
  }
}
</style>
