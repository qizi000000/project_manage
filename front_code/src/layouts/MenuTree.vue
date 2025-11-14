<template>
  <!-- 递归菜单组件：支持多级折叠；左侧图标+文字，右侧自定义展开/收起箭头 -->
  <div style="display: contents">
    <template v-for="item in filteredItems">
    <!-- 父级菜单（包含子菜单时使用 q-expansion-item） -->
    <q-expansion-item
      v-if="item.children && item.children.length"
      :key="(item.path || item.label) + '-group'"
      expand-separator
      hide-expand-icon
      :default-opened="item.expanded"
    >
      <!-- 自定义 header：左图标 / 中文字 / 右箭头；隐藏内置箭头避免重复 -->
      <template #header="scope">
        <q-item-section avatar v-if="item.icon" :data-label="item.label">
          <q-icon :name="item.icon" />
        </q-item-section>
        <q-item-section class="q-mini-drawer-hide">
          <q-item-label>{{ item.label }}</q-item-label>
        </q-item-section>
        <q-item-section side class="q-mini-drawer-hide">
          <q-icon
            :name="scope.expanded ? 'keyboard_arrow_down' : 'keyboard_arrow_right'"
            class="cursor-pointer"
            @click.stop="scope.toggle"
          />
        </q-item-section>
      </template>
      <!-- 子菜单整体相对父菜单右移一个"tab"（indent 像素） -->
      <div :style="{ paddingLeft: indent + 'px' }">
        <menu-tree :items="item.children" :indent="indent" :level="level + 1" />
      </div>
    </q-expansion-item>

    <!-- 叶子菜单项（无子菜单）：支持按层级设置紧凑行高 -->
  <q-item v-else :key="(item.path || item.label) + '-leaf'" :to="item.path" :exact="item.exact === true" clickable v-ripple :data-label="item.label">
      <q-item-section avatar v-if="item.icon">
        <q-icon :name="item.icon" />
      </q-item-section>
      <q-item-section class="q-mini-drawer-hide">{{ item.label }}</q-item-section>
    </q-item>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAuthStore } from '../stores/auth'

// Props 说明：
// - items: 菜单数据，形如 [{ label, icon?, path?, children?, permissions? }]；有 children 视为父级项
// - indent: 子菜单相对父菜单右移的像素（一个"tab"），默认 16
// - level: 当前层级，顶级为 0；用于控制 dense 与递归层次
// - hasPermission: 权限检查函数，接收权限码数组，返回是否有权限
const props = defineProps({
  items: {
    type: Array,
    default: () => [],
  },
  // 每一层相对父菜单右移的像素（一个"tab"）
  indent: {
    type: Number,
    default: 16,
  },
  // 当前层级（顶级为 0）
  level: {
    type: Number,
    default: 0,
  },
})

const authStore = useAuthStore()

// 过滤有权限的菜单项
const filteredItems = computed(() => {
  return props.items.filter(item => {
    // 如果没有设置权限要求，则显示
    if (!item.permissions || item.permissions.length === 0) {
      return true
    }

    // 检查是否有任一所需权限
    return item.permissions.some(permission => authStore.hasPermission(permission))
  })
})
</script>

<style scoped>
/* Mini模式下的菜单项样式 */
:deep(.q-drawer--mini) .q-item {
  justify-content: center;
  padding: 12px 8px;
}

:deep(.q-drawer--mini) .q-item:hover {
  background-color: rgba(var(--q-primary-rgb), 0.1);
}

/* Mini模式下的tooltip */
:deep(.q-drawer--mini) .q-item:hover::after {
  content: attr(data-label);
  position: absolute;
  left: 100%;
  top: 50%;
  transform: translateY(-50%);
  background: var(--q-dark);
  color: white;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 14px;
  white-space: nowrap;
  z-index: 2000;
  margin-left: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

:deep(.q-drawer--mini) .q-item:hover::before {
  content: '';
  position: absolute;
  left: 100%;
  top: 50%;
  transform: translateY(-50%) translateX(-4px);
  width: 0;
  height: 0;
  border-top: 4px solid transparent;
  border-bottom: 4px solid transparent;
  border-right: 4px solid var(--q-dark);
  z-index: 2001;
}
</style>