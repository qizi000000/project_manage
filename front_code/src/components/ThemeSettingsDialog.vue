<template>
  <q-dialog v-model="dialogVisible" persistent>
    <q-card class="theme-dialog-card" style="min-width: 450px; max-width: 500px;">
      <q-card-section class="theme-dialog-header">
        <div class="row items-center">
          <q-icon name="palette" size="24px" color="primary" class="q-mr-sm" />
          <div class="text-h6 text-weight-medium">主题设置</div>
        </div>
        <q-space />
        <q-btn flat round dense icon="close" @click="closeDialog" class="close-btn" />
      </q-card-section>

      <q-separator />

      <q-card-section class="theme-dialog-content">
        <!-- 明暗模式选择 -->
        <div class="theme-section">
          <div class="section-title">
            <q-icon name="brightness_6" size="18px" color="primary" class="q-mr-xs" />
            <span class="text-subtitle1 text-weight-medium">明暗模式</span>
          </div>
          <div class="dark-mode-options">
            <div
              v-for="option in darkModeOptions"
              :key="option.value"
              :class="['dark-mode-option', { active: currentDarkMode === option.value }]"
              @click="updateDarkMode(option.value)"
            >
              <q-icon :name="getDarkModeIcon(option.value)" size="20px" class="option-icon" />
              <span class="option-label">{{ option.label }}</span>
            </div>
          </div>
        </div>

        <q-separator class="section-separator" />

        <!-- 主题色选择 -->
        <div class="theme-section">
          <div class="section-title">
            <q-icon name="color_lens" size="18px" color="primary" class="q-mr-xs" />
            <span class="text-subtitle1 text-weight-medium">主题配色</span>
          </div>
          <div class="color-theme-options">
            <div
              v-for="theme in colorThemeOptions"
              :key="theme.value"
              :class="['color-theme-option', { active: currentColorTheme === theme.value }]"
              @click="updateColorTheme(theme.value)"
            >
              <div class="color-preview" :style="{ background: theme.previewColor }"></div>
              <div class="color-label">{{ theme.label }}</div>
              <q-icon v-if="currentColorTheme === theme.value" name="check" size="16px" class="check-icon" />
            </div>
          </div>
        </div>
      </q-card-section>

      <q-card-actions class="theme-dialog-actions q-pa-md">
        <q-space />
        <q-btn
          flat
          label="关闭"
          color="grey-7"
          @click="closeDialog"
          class="action-btn"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useQuasar } from 'quasar'

// Props
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['update:modelValue'])

const $q = useQuasar()

// 内部对话框显示状态
const dialogVisible = ref(false)

// 监听modelValue变化，同步到内部状态
watch(() => props.modelValue, (newValue) => {
  dialogVisible.value = newValue
}, { immediate: true })

// 监听内部状态变化，emit到父组件
watch(dialogVisible, (newValue) => {
  emit('update:modelValue', newValue)
})

// 主题设置数据
const currentDarkMode = ref($q.dark.isActive ? 'dark' : 'light')
const currentColorTheme = ref(localStorage.getItem('colorTheme') || 'blue')

const darkModeOptions = [
  { label: '自动', value: 'auto' },
  { label: '浅色', value: 'light' },
  { label: '深色', value: 'dark' }
]

const colorThemeOptions = [
  { label: '蓝色', value: 'blue', previewColor: '#1976d2' },
  { label: '绿色', value: 'green', previewColor: '#4caf50' },
  { label: '紫色', value: 'purple', previewColor: '#9c27b0' },
  { label: '橙色', value: 'orange', previewColor: '#ff9800' },
  { label: '粉色', value: 'pink', previewColor: '#e91e63' }
]

// 更新明暗模式
function updateDarkMode(value) {
  currentDarkMode.value = value
  if (value === 'auto') {
    $q.dark.set('auto')
  } else {
    $q.dark.set(value === 'dark')
  }
  localStorage.setItem('darkMode', value)
}

// 更新主题颜色
function updateColorTheme(theme) {
  currentColorTheme.value = theme
  localStorage.setItem('colorTheme', theme)

  // 更新CSS变量
  const root = document.documentElement
  const themeColors = {
    blue: { primary: '#1976d2', secondary: '#424242', accent: '#82b1ff' },
    green: { primary: '#4caf50', secondary: '#424242', accent: '#c8e6c9' },
    purple: { primary: '#9c27b0', secondary: '#424242', accent: '#e1bee7' },
    orange: { primary: '#ff9800', secondary: '#424242', accent: '#ffe0b2' },
    pink: { primary: '#e91e63', secondary: '#424242', accent: '#fce4ec' }
  }

  const colors = themeColors[theme]

  // 辅助函数：将hex颜色转换为RGB
  function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
    return result ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}` : null
  }

  root.style.setProperty('--q-primary', colors.primary)
  root.style.setProperty('--q-primary-rgb', hexToRgb(colors.primary))
  root.style.setProperty('--q-secondary', colors.secondary)
  root.style.setProperty('--q-accent', colors.accent)
}

// 获取明暗模式图标
function getDarkModeIcon(mode) {
  switch (mode) {
    case 'auto':
      return 'brightness_auto'
    case 'light':
      return 'brightness_high'
    case 'dark':
      return 'brightness_2'
    default:
      return 'brightness_auto'
  }
}

// 关闭对话框
function closeDialog() {
  dialogVisible.value = false
}

// 初始化主题设置
onMounted(() => {
  const savedDarkMode = localStorage.getItem('darkMode') || 'auto'
  const savedColorTheme = localStorage.getItem('colorTheme') || 'blue'

  currentDarkMode.value = savedDarkMode
  currentColorTheme.value = savedColorTheme

  // 应用暗色模式
  if (savedDarkMode === 'auto') {
    $q.dark.set('auto')
  } else {
    $q.dark.set(savedDarkMode === 'dark')
  }

  // 应用颜色主题
  updateColorTheme(savedColorTheme)
})
</script>

<style scoped>
/* 主题对话框样式 */
.theme-dialog-card {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
}

.theme-dialog-header {
  background: linear-gradient(135deg, var(--q-primary) 0%, var(--q-primary-rgb, 25, 118, 210) 100%);
  color: white;
  padding: 1.25rem 1.5rem;
}

.theme-dialog-header .text-h6 {
  color: white;
}

.close-btn {
  color: white;
}

.close-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.theme-dialog-content {
  padding: 1.5rem;
}

.theme-section {
  margin-bottom: 1.5rem;
}

.section-title {
  display: flex;
  align-items: center;
  margin-bottom: 1rem;
  color: var(--q-primary);
}

.dark-mode-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: 0.75rem;
}

.dark-mode-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem 0.75rem;
  border-radius: 12px;
  border: 2px solid var(--q-separator-color);
  background: var(--q-card-background);
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
}

.dark-mode-option:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: var(--q-primary);
}

.dark-mode-option.active {
  border-color: var(--q-primary);
  background: rgba(var(--q-primary-rgb), 0.08);
  box-shadow: 0 4px 16px rgba(var(--q-primary-rgb), 0.2);
}

.option-icon {
  margin-bottom: 0.5rem;
  color: var(--q-primary);
}

.option-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--q-text-color);
}

.section-separator {
  margin: 1.5rem 0;
  background: var(--q-separator-color);
}

.color-theme-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(90px, 1fr));
  gap: 0.75rem;
}

.color-theme-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem 0.5rem;
  border-radius: 12px;
  border: 2px solid var(--q-separator-color);
  background: var(--q-card-background);
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  text-align: center;
}

.color-theme-option:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: var(--q-primary);
}

.color-theme-option.active {
  border-color: var(--q-primary);
  background: rgba(var(--q-primary-rgb), 0.08);
  box-shadow: 0 4px 16px rgba(var(--q-primary-rgb), 0.2);
}

.color-preview {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  margin-bottom: 0.5rem;
  border: 2px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.color-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--q-text-color);
  margin-bottom: 0.25rem;
}

.check-icon {
  position: absolute;
  top: 8px;
  right: 8px;
  color: white;
  background: var(--q-primary);
  border-radius: 50%;
  padding: 2px;
}

.theme-dialog-actions {
  background: var(--q-card-background);
  border-top: 1px solid var(--q-separator-color);
}

.action-btn {
  border-radius: 8px;
  font-weight: 500;
}
</style>