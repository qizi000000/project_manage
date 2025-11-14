<template>
  <div>
    <!-- 顶部工具栏：搜索/全选/清空 -->
    <div class="row items-center q-col-gutter-sm q-mb-sm">
      <div class="col">
        <q-input v-model="keyword" dense clearable outlined placeholder="搜索权限（名称/键）">
          <template #prepend><q-icon name="search" /></template>
        </q-input>
      </div>
      <div class="col-auto">
        <q-btn flat color="primary" label="全选可见" @click="checkAllVisible(true)" />
        <q-btn flat color="primary" label="清空可见" @click="checkAllVisible(false)" />
      </div>
    </div>

    <!-- 分组列表 -->
    <q-list bordered separator>
      <div v-for="group in filteredGroups" :key="group.key">
        <q-expansion-item :label="group.label" expand-separator>
          <template #header>
            <q-item-section>{{ group.label }}</q-item-section>
            <q-item-section side>
              <q-btn size="sm" flat dense label="全选分组" @click.stop="checkGroup(group, true)" />
              <q-btn size="sm" flat dense label="清空分组" @click.stop="checkGroup(group, false)" />
            </q-item-section>
          </template>

          <div class="row q-col-gutter-sm q-pa-sm">
            <div v-for="perm in group.items" :key="perm.key" class="col-12 col-sm-6 col-md-4">
              <q-checkbox v-model="checkedSetMap[group.key]" :val="perm.key" :label="perm.label" />
              <div class="text-grey-7 text-caption q-ml-lg">{{ perm.key }}</div>
            </div>
          </div>
        </q-expansion-item>
      </div>
    </q-list>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  // 分组权限数据：[{ key, label, items: [{ key, label }] }]
  groups: { type: Array, default: () => [] },
  // 选中值（权限 key 数组）
  modelValue: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue'])

const keyword = ref('')
// 以分组 key 为键保存 Set 形式的选中项，便于组内操作
const checkedSetMap = reactive({})

// 初始化/同步选中
watch(() => props.modelValue, (vals) => {
  const all = new Set(vals)
  for (const g of props.groups) {
    checkedSetMap[g.key] = new Set((checkedSetMap[g.key] || []))
    const groupKeys = g.items.map(i => i.key)
    checkedSetMap[g.key] = new Set(groupKeys.filter(k => all.has(k)))
  }
}, { immediate: true })

// 输出为扁平数组
const flatChecked = computed(() => {
  const out = []
  for (const g of props.groups) {
    const s = checkedSetMap[g.key] || new Set()
    out.push(...Array.from(s))
  }
  return out
})

watch(flatChecked, (vals) => emit('update:modelValue', vals))

// 过滤分组/权限（支持名称和 key）
const filteredGroups = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return props.groups
  return props.groups.map(g => {
    const items = g.items.filter(i => (i.label + i.key).toLowerCase().includes(kw))
    return { ...g, items }
  }).filter(g => g.items.length)
})

function checkAllVisible(flag) {
  for (const g of filteredGroups.value) {
    checkGroup(g, flag)
  }
}

function checkGroup(group, flag) {
  const set = new Set(checkedSetMap[group.key] || [])
  for (const p of group.items) {
    if (flag) set.add(p.key)
    else set.delete(p.key)
  }
  checkedSetMap[group.key] = set
}
</script>
