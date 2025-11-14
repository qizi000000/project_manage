<template>
  <q-card flat bordered>
    <q-card-section class="row items-center">
      <div class="text-subtitle2">{{ title }}</div>
      <q-space />
      <q-btn flat dense icon="refresh" @click="fetchAttachments" />
    </q-card-section>
    <q-separator />
    <q-card-section>
      <!-- 上传组件 -->
      <q-file
        v-model="uploadFile"
        label="拖拽文件到此处或点击选择文件"
        outlined
        counter
        max-file-size="52428800"
        @update:model-value="handleFileUpload"
        @rejected="onFileRejected"
        class="q-mb-md"
        style="min-height: 100px;"
        :disable="!canUpload"
      >
        <template v-slot:prepend>
          <q-icon name="cloud_upload" size="lg" />
        </template>
        <template v-slot:hint>
          支持所有文件格式，单个文件最大 50MB
        </template>
      </q-file>

      <!-- 附件列表 -->
      <q-list bordered separator v-if="attachments.length">
        <q-item v-for="a in attachments" :key="a.id" class="q-py-md">
          <q-item-section avatar>
            <q-avatar color="blue-1" text-color="primary">
              <q-icon name="description" />
            </q-avatar>
          </q-item-section>
          <q-item-section>
            <q-item-label class="text-subtitle2 text-weight-medium">{{ a.filename }}</q-item-label>
            <q-item-label caption class="q-mt-xs">
              <q-icon name="person" size="16px" color="grey-6" />
              <span class="text-grey-7">{{ a.uploader_name || '未知' }}</span>
            </q-item-label>
            <q-item-label caption class="q-mt-xs" style="white-space: nowrap;">
              <q-icon name="access_time" size="16px" color="grey-6" />
              <span class="text-grey-7">{{ formatDate(a.uploaded_at) }}</span>
              <span class="text-grey-5 q-mx-sm">|</span>
              <q-icon name="storage" size="16px" color="grey-6" />
              <span class="text-grey-7">{{ formatFileSize(a.file_size) }}</span>
            </q-item-label>
          </q-item-section>
          <q-item-section side>
            <div class="row items-center q-gutter-xs">
              <q-btn flat dense round size="sm" icon="download" color="primary" @click="downloadFile(a)">
                <q-tooltip>下载</q-tooltip>
              </q-btn>
              <q-btn
                v-if="canDelete"
                flat
                dense
                round
                size="sm"
                icon="delete"
                color="negative"
                @click="deleteAttachment(a.id)"
              >
                <q-tooltip>删除</q-tooltip>
              </q-btn>
            </div>
          </q-item-section>
        </q-item>
      </q-list>
      <div v-else class="text-grey q-pa-sm">暂无附件</div>
    </q-card-section>
  </q-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'

// Props
const props = defineProps({
  title: {
    type: String,
    default: '附件管理'
  },
  apiBasePath: {
    type: String,
    required: true // 如 '/projects/123' 或 '/tasks/456'
  },
  canUpload: {
    type: Boolean,
    default: true
  },
  canDelete: {
    type: Boolean,
    default: true
  }
})

// Emits
const emit = defineEmits(['attachment-updated'])

// 响应式数据
const attachments = ref([])
const uploadFile = ref(null)
const $q = useQuasar()

// 获取附件列表
async function fetchAttachments() {
  try {
    const { data } = await api.get(`${props.apiBasePath}/attachments`)
    attachments.value = data
  } catch (error) {
    console.error('获取附件列表失败:', error)
    $q.notify({
      type: 'negative',
      message: '获取附件列表失败',
      position: 'top'
    })
  }
}

// 处理文件上传
async function handleFileUpload(file) {
  if (!file) return

  try {
    const formData = new FormData()
    formData.append('file', file)

    await api.post(`${props.apiBasePath}/attachments`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    $q.notify({ type: 'positive', message: '文件上传成功', position: 'top' })
    uploadFile.value = null // 清空选择
    await fetchAttachments() // 刷新列表
    emit('attachment-updated')
  } catch (error) {
    console.error('上传失败:', error)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || '上传失败',
      position: 'top'
    })
  }
}

// 删除附件
async function deleteAttachment(attachmentId) {
  $q.dialog({
    title: '确认删除',
    message: '确定要删除此附件吗？',
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      // 根据apiBasePath确定删除API路径
      const deletePath = props.apiBasePath.startsWith('/projects/')
        ? `/projects/attachments/${attachmentId}`
        : `/tasks/attachments/${attachmentId}`
      await api.delete(deletePath)
      $q.notify({ type: 'positive', message: '附件删除成功', position: 'top' })
      await fetchAttachments()
      emit('attachment-updated')
    } catch (error) {
      console.error('删除失败:', error)
      $q.notify({
        type: 'negative',
        message: error.response?.data?.detail || '删除失败',
        position: 'top'
      })
    }
  })
}

// 文件上传被拒绝时的处理
function onFileRejected(rejectedEntries) {
  const file = rejectedEntries[0]
  if (file.failedPropValidation === 'max-file-size') {
    $q.notify({
      type: 'negative',
      message: '文件大小超过限制（最大50MB）',
      position: 'top'
    })
  }
}

// 下载文件
function downloadFile(attachment) {
  // 创建隐藏的 a 标签触发下载
  const link = document.createElement('a')
  link.href = attachment.url
  link.download = attachment.filename
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// 工具函数
function formatDate(val) {
  if (!val) return '—'
  try {
    return new Date(val).toLocaleString()
  } catch {
    return String(val)
  }
}

function formatFileSize(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

// 初始化
onMounted(() => {
  fetchAttachments()
})

// 暴露方法给父组件
defineExpose({
  fetchAttachments,
  attachments
})
</script>