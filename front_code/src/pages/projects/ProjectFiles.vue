<template>
  <q-page padding>
    <div class="q-gutter-md">
      <div class="row items-center q-mb-md">
        <div class="text-h6">项目文件</div>
        <q-space />
        <q-select
          v-if="!route.params.id"
          v-model="selectedProject"
          :options="projectOptions"
          option-value="value"
          option-label="label"
          map-options
          emit-value
          label="选择项目"
          class="q-mr-md"
          style="min-width: 200px"
          @update:model-value="onProjectChange"
        />
      </div>
      <!-- 上传区域 -->
      <q-card>
        <q-card-section>
          <div class="text-h6">上传附件</div>
        </q-card-section>
        
        <q-card-section>
          <q-uploader
            url="/api/projects/:id/attachments"
            label="拖拽文件到此处或点击选择"
            multiple
            auto-upload
            :factory="uploadFactory"
            @uploaded="onUploaded"
            @failed="onFailed"
            class="full-width"
            style="max-width: 100%"
          >
            <template v-slot:header="scope">
              <div class="row no-wrap items-center q-pa-sm q-gutter-xs">
                <q-btn
                  v-if="scope.queuedFiles.length > 0"
                  icon="clear_all"
                  @click="scope.removeQueuedFiles"
                  round
                  dense
                  flat
                >
                  <q-tooltip>清除队列</q-tooltip>
                </q-btn>
                <q-btn
                  v-if="scope.uploadedFiles.length > 0"
                  icon="done_all"
                  @click="scope.removeUploadedFiles"
                  round
                  dense
                  flat
                >
                  <q-tooltip>清除已上传</q-tooltip>
                </q-btn>
                <q-spinner v-if="scope.isUploading" class="q-uploader__spinner" />
                <div class="col">
                  <div class="q-uploader__title">上传文件</div>
                  <div class="q-uploader__subtitle">
                    {{ scope.uploadSizeLabel }} / {{ scope.uploadProgressLabel }}
                  </div>
                </div>
                <q-btn
                  v-if="scope.canAddFiles"
                  type="a"
                  icon="add_box"
                  @click="scope.pickFiles"
                  round
                  dense
                  flat
                >
                  <q-uploader-add-trigger />
                  <q-tooltip>选择文件</q-tooltip>
                </q-btn>
                <q-btn
                  v-if="scope.canUpload"
                  icon="cloud_upload"
                  @click="scope.upload"
                  round
                  dense
                  flat
                >
                  <q-tooltip>上传文件</q-tooltip>
                </q-btn>

                <q-btn
                  v-if="scope.isUploading"
                  icon="clear"
                  @click="scope.abort"
                  round
                  dense
                  flat
                >
                  <q-tooltip>中止上传</q-tooltip>
                </q-btn>
              </div>
            </template>
          </q-uploader>
        </q-card-section>
      </q-card>

      <!-- 文件列表 -->
      <q-card>
        <q-card-section>
          <div class="text-h6">附件列表</div>
        </q-card-section>
        
        <q-separator />
        
        <q-card-section v-if="loading">
          <q-spinner color="primary" size="3em" />
        </q-card-section>
        
        <q-list v-else-if="attachments.length > 0" separator>
          <q-item v-for="file in attachments" :key="file.id" clickable>
            <q-item-section avatar>
              <q-icon :name="getFileIcon(file.filename)" color="primary" size="md" />
            </q-item-section>
            
            <q-item-section>
              <q-item-label>{{ file.filename }}</q-item-label>
              <q-item-label caption>
                上传于 {{ formatDate(file.uploaded_at) }}
              </q-item-label>
            </q-item-section>
            
            <q-item-section side>
              <div class="q-gutter-sm">
                <q-btn
                  icon="download"
                  flat
                  round
                  dense
                  color="primary"
                  @click="downloadFile(file)"
                >
                  <q-tooltip>下载</q-tooltip>
                </q-btn>
                <q-btn
                  v-if="canDelete(file)"
                  icon="delete"
                  flat
                  round
                  dense
                  color="negative"
                  @click="deleteFile(file)"
                >
                  <q-tooltip>删除</q-tooltip>
                </q-btn>
              </div>
            </q-item-section>
          </q-item>
        </q-list>
        
        <q-card-section v-else>
          <div class="text-center text-grey">暂无附件</div>
        </q-card-section>
      </q-card>
    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted  } from 'vue';
import { useRoute } from 'vue-router';
import { useQuasar } from 'quasar';
import { api, apiBaseURL } from 'boot/axios';

const route = useRoute();
const $q = useQuasar();

const projectId = ref(route.params.id || null);
const attachments = ref([]);
const loading = ref(false);
const selectedProject = ref(null);
const projectOptions = ref([]);

// 获取当前用户信息
const currentUser = ref(null);
const userRole = ref(null);

// 加载项目选项
async function loadProjects(){
  try{
    const { data } = await api.get('/projects/', { params: { page_size: 100 } })
    projectOptions.value = (data.items || []).map(p => ({ label: p.name, value: p.id }))
    if(projectOptions.value.length && !projectId.value){
      selectedProject.value = projectOptions.value[0].value
      projectId.value = selectedProject.value
    }
  }catch(e){
    console.error('加载项目失败', e)
  }
}

function onProjectChange(val){
  projectId.value = val
  loadAttachments()
}

onMounted(async () => {
  if(!route.params.id){
    await loadProjects()
  }
  await loadCurrentUser();
  await loadAttachments();
});

async function loadCurrentUser() {
  try {
    const res = await api.get('/auth/me');
    currentUser.value = res.data;
    userRole.value = res.data.role_name || (res.data.is_admin ? '管理员' : null);
  } catch (error) {
    console.error('获取用户信息失败', error);
  }
}

async function loadAttachments() {
  loading.value = true;
  try {
    const res = await api.get(`/projects/${projectId.value}/attachments`);
    attachments.value = res.data;
  } catch {
    $q.notify({
      type: 'negative',
      message: '加载附件列表失败'
    });
  } finally {
    loading.value = false;
  }
}

// 上传工厂函数
function uploadFactory() {
  const token = localStorage.getItem('token')
  return {
    url: `${apiBaseURL}/projects/${projectId.value}/attachments`,
    method: 'POST',
    headers: [
      {
        name: 'Authorization',
        value: `Bearer ${token}`
      }
    ],
    fieldName: 'file'
  };
}

function onUploaded() {
  $q.notify({
    type: 'positive',
    message: '文件上传成功'
  });
  loadAttachments();
}

function onFailed() {
  $q.notify({
    type: 'negative',
    message: '文件上传失败'
  });
}

async function downloadFile(file) {
  try {
    const response = await api.get(`/projects/attachments/${file.id}/download`, {
      responseType: 'blob'
    });
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', file.filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  } catch {
    $q.notify({
      type: 'negative',
      message: '下载失败'
    });
  }
}

async function deleteFile(file) {
  $q.dialog({
    title: '确认删除',
    message: `确定要删除文件 "${file.filename}" 吗？`,
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await api.delete(`/projects/attachments/${file.id}`);
      $q.notify({
        type: 'positive',
        message: '删除成功'
      });
      loadAttachments();
    } catch (error) {
      $q.notify({
        type: 'negative',
        message: error.response?.data?.detail || '删除失败'
      });
    }
  });
}

function canDelete(file) {
  if (!currentUser.value) return false;
  
  // 管理员可以删除
  if (userRole.value === '管理员') return true;
  
  // 上传者可以删除
  if (file.uploaded_by === currentUser.value.id) return true;
  
  // TODO: 项目负责人可以删除（需要从项目信息中获取）
  return false;
}

function getFileIcon(filename) {
  const ext = filename.split('.').pop().toLowerCase();
  
  const iconMap = {
    // 文档
    pdf: 'picture_as_pdf',
    doc: 'description',
    docx: 'description',
    txt: 'description',
    
    // 表格
    xls: 'grid_on',
    xlsx: 'grid_on',
    csv: 'grid_on',
    
    // 图片
    jpg: 'image',
    jpeg: 'image',
    png: 'image',
    gif: 'image',
    svg: 'image',
    
    // 压缩包
    zip: 'folder_zip',
    rar: 'folder_zip',
    '7z': 'folder_zip',
    
    // 代码
    js: 'code',
    ts: 'code',
    py: 'code',
    java: 'code',
    cpp: 'code',
    c: 'code',
    vue: 'code',
    
    // 其他
    ppt: 'slideshow',
    pptx: 'slideshow',
    mp4: 'video_file',
    mp3: 'audio_file'
  };
  
  return iconMap[ext] || 'insert_drive_file';
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleString('zh-CN');
}
</script>

<style scoped>
.q-uploader {
  min-height: 200px;
}
</style>
