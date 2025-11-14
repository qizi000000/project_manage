<template>
  <q-page padding>
    <div class="text-h6 q-mb-md">创建角色</div>
    <q-form @submit.prevent="onSubmit" @reset.prevent="onReset">
      <q-card flat bordered class="q-mb-md">
        <q-card-section class="row q-col-gutter-md">
          <div class="col-12 col-md-6">
            <q-input v-model="form.name" label="角色名称" outlined dense :rules="[v=>!!v||'必填']" />
          </div>
          <div class="col-12 col-md-6">
            <q-input v-model="form.desc" label="角色描述" outlined dense />
          </div>
        </q-card-section>
      </q-card>

      <q-card flat bordered>
        <q-card-section class="text-subtitle1">权限配置</q-card-section>
        <q-separator />
        <q-card-section>
          <PermissionMatrix v-model="form.permissions" :groups="permissionGroups" />
        </q-card-section>
      </q-card>

      <div class="q-mt-md">
        <q-btn type="submit" color="primary" label="保存" class="q-mr-sm" />
        <q-btn type="reset" flat label="重置" />
      </div>
    </q-form>
  </q-page>
</template>

<script setup>
import { reactive } from 'vue'
import PermissionMatrix from 'components/PermissionMatrix.vue'

const form = reactive({
  name: '',
  desc: '',
  permissions: [],
})

// 示例权限分组（后续替换为后端返回）
const permissionGroups = [
  {
    key: 'project',
    label: '项目',
    items: [
      { key: 'project.read', label: '查看项目' },
      { key: 'project.create', label: '创建项目' },
      { key: 'project.update', label: '编辑项目' },
      { key: 'project.delete', label: '删除项目' },
    ],
  },
  {
    key: 'task',
    label: '任务',
    items: [
      { key: 'task.read', label: '查看任务' },
      { key: 'task.create', label: '创建任务' },
      { key: 'task.update', label: '编辑任务' },
      { key: 'task.delete', label: '删除任务' },
    ],
  },
  {
    key: 'team',
    label: '团队',
    items: [
      { key: 'team.read', label: '查看团队' },
      { key: 'team.member.manage', label: '管理成员' },
      { key: 'team.role.manage', label: '管理角色权限' },
      { key: 'team.project.link', label: '关联项目' },
    ],
  },
]

function onSubmit() {
  // TODO: 调用创建角色 API
  console.log('submit role', JSON.parse(JSON.stringify(form)))
}
function onReset() {
  form.name = ''
  form.desc = ''
  form.permissions = []
}
</script>
