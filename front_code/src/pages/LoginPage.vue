<template>
  <q-page class="login-page column items-center justify-center">
    <div class="brand q-mb-xl">
      <q-avatar size="64px" class="q-mr-sm">
        <img src="/icons/favicon-128x128.png" alt="logo" />
      </q-avatar>
      <div class="text-h5 text-bold text-white">项目管理系统</div>
    </div>

    <q-card class="login-card glass" flat>
      <q-card-section>
        <div class="text-h6 q-mb-sm">欢迎登录</div>
        <div class="text-caption text-grey-6">请使用账号密码登录</div>
      </q-card-section>
      <q-separator inset />
      <q-card-section>
        <q-form @submit.prevent="onSubmit">
          <q-input dark v-model="form.username" label="用户名" outlined dense clearable lazy-rules :rules="[v=>!!v||'请输入用户名']" class="q-mb-md" label-color="grey-3" input-class="text-white">
            <template #prepend><q-icon name="person_outline" /></template>
          </q-input>
          <q-input dark v-model="form.password" :type="showPwd ? 'text' : 'password'" label="密码" outlined dense clearable lazy-rules :rules="[v=>!!v||'请输入密码']" label-color="grey-3" input-class="text-white">
            <template #prepend><q-icon name="lock_outline" /></template>
            <template #append>
              <q-icon :name="showPwd ? 'visibility' : 'visibility_off'" class="cursor-pointer" @click="showPwd=!showPwd" />
            </template>
          </q-input>
          <div class="row items-center justify-between q-mt-sm">
            <q-checkbox v-model="form.remember" label="记住我" dense class="text-grey-4" />
            <q-btn flat padding="xs" color="primary" label="忘记密码?" @click="onForgot" />
          </div>
          <q-btn type="submit" color="primary" label="登录" class="full-width q-mt-md" unelevated />
        </q-form>
      </q-card-section>
    </q-card>

    <div class="text-grey-5 text-caption q-mt-lg">© 2025 Your Company</div>
  </q-page>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'

const form = reactive({ username: '', password: '', remember: true })
const showPwd = ref(false)
const router = useRouter()
const route = useRoute()
const $q = useQuasar()

// 页面加载时从 localStorage 恢复用户名
onMounted(() => {
  const savedUsername = localStorage.getItem('rememberedUsername')
  const savedPassword = localStorage.getItem('rememberedPassword')
  if (savedUsername) {
    form.username = savedUsername
    form.remember = true
  }
  if (savedPassword) {
    form.password = savedPassword
  }
})

async function onSubmit(){
  try {
    const { data } = await api.post('/auth/login', { username: form.username, password: form.password })
    // 保存 token
    localStorage.setItem('token', data.access_token)
    // 设置到 axios header（简化处理）
    api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`
    
    // 处理记住我功能
    if (form.remember) {
      localStorage.setItem('rememberedUsername', form.username)
      localStorage.setItem('rememberedPassword', form.password)
    } else {
      localStorage.removeItem('rememberedUsername')
      localStorage.removeItem('rememberedPassword')
    }
    
    // 跳转：优先返回 redirect
    const redirect = route.query.redirect ? decodeURIComponent(route.query.redirect) : '/'
    router.push(redirect)
  } catch (e) {
  const status = e?.response?.status
  const detail = e?.response?.data?.detail
  const msg = detail || (status === 403 ? '账号已被禁用' : status === 400 ? '用户名或密码错误' : '登录失败，请稍后重试')
  $q.notify({ type: 'negative', message: msg, icon: 'error' })
  }
}
function onForgot(){
  // TODO: 忘记密码流程
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  padding: 32px 16px;
  background: radial-gradient(1200px 600px at 10% 10%, rgba(99,102,241,0.25), transparent 60%),
              radial-gradient(800px 400px at 90% 20%, rgba(16,185,129,0.2), transparent 60%),
              linear-gradient(135deg, #0f1220, #0b1020 40%, #0a0e1a);
}
.brand { display: flex; align-items: center; }
.login-card { width: 100%; max-width: 420px; }
/* 玻璃拟态效果 */
.glass {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.12);
  box-shadow: 0 10px 40px rgba(2,6,23,0.45);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border-radius: 14px;
}
/* 输入框占位符颜色在深色背景下更可读 */
.login-card ::placeholder { color: rgba(255,255,255,0.6); }
</style>
