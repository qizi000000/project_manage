<template>
  <q-drawer
    show-if-above
    v-model="drawerModel"
    side="left"
    elevated
    :mini="!drawerModel || miniState"
    :mini-width="60"
    class="fixed-drawer"
  >
    <q-scroll-area class="fit">
      <q-list padding>
       
        <menu-tree :items="menuItems" />
      </q-list>
    </q-scroll-area>

    <!-- 菜单折叠按钮 -->
    <div class="drawer-footer">
      <q-btn
        flat
        :icon="drawerModel && !miniState ? 'chevron_left' : 'menu'"
        class="collapse-btn"
        @click="handleDrawerToggle"
      >
        <q-tooltip v-if="!drawerModel || miniState">{{ miniState ? '展开菜单' : '展开菜单' }}</q-tooltip>
      </q-btn>
    </div>
  </q-drawer>
</template>

<script setup>
import { ref, computed } from 'vue'
import MenuTree from '../layouts/MenuTree.vue'


// Props
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  menuItems: {
    type: Array,
    default: () => []
  }
})

// Emits
const emit = defineEmits(['update:modelValue'])

// 内部状态
const miniState = ref(false)

// 使用computed来处理双向绑定
const drawerModel = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 处理drawer切换
function handleDrawerToggle() {
  if (drawerModel.value && !miniState.value) {
    // 当前drawer打开且不在mini模式，点击进入mini模式
    miniState.value = true
  } else {
    // 其他情况都展开drawer并退出mini模式
    drawerModel.value = true
    miniState.value = false
  }
}
</script>

<style scoped>
.fixed-drawer {
  position: fixed !important;
  top: 64px !important; /* header高度 */
  left: 0 !important;
  width: 200px !important;
}

/* 抽屉底部按钮区域 */
.drawer-footer {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px;
  border-top: 1px solid var(--q-separator-color);
  background: var(--q-card-background);
}

.collapse-btn {
  width: 100%;
  justify-content: center;
  color: var(--q-primary) !important;
}

.collapse-btn:hover {
  background-color: rgba(var(--q-primary-rgb), 0.1) !important;
}
</style>