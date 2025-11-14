<template>
  <q-select
    v-model="model"
    :options="options"
    option-value="id"
    option-label="name"
    emit-value
    map-options
    dense
    outlined
    label="当前团队"
    @update:model-value="onChange"
  />
</template>

<script setup>
import { watch, ref, onMounted } from 'vue'
import { useTeamStore } from 'stores/team/useTeamStore'
import { api } from 'boot/axios'

const props = defineProps({
  modelValue: [String, Number, null],
})
const emit = defineEmits(['update:modelValue', 'change'])

const store = useTeamStore()
const options = ref([])
const model = ref(props.modelValue ?? store.currentTeamId)

watch(() => props.modelValue, v => (model.value = v))

function onChange(val) {
  store.setCurrentTeam(val)
  emit('update:modelValue', val)
  emit('change', val)
}

onMounted(async () => {
  try {
    const { data } = await api.get('/teams/', { params: { page: 1, page_size: 100 } })
    const items = Array.isArray(data?.items) ? data.items : []
    options.value = items
    // 同步到 store，供其它页面使用
    store.teams = items
  } catch {
    options.value = []
  }
  if (!model.value) {
    model.value = store.currentTeamId || options.value[0]?.id || null
    if (model.value) {
      store.setCurrentTeam(model.value)
    }
  }
})
</script>
