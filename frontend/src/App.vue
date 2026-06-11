<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'

const route = useRoute()
const router = useRouter()

// 登录/注册页面不需要侧边栏布局
const isAuthPage = computed(
  () => route.path === '/login' || route.path === '/register'
)

// 等待路由初始化完成后再渲染，避免布局闪烁
const isAppReady = ref(false)
router.isReady().then(() => {
  isAppReady.value = true
})
</script>

<template>
  <!-- 路由未就绪时展示渐变背景，与登录页一致，避免白屏 -->
  <div v-if="!isAppReady" class="app-loading" />
  <template v-else>
    <!-- 认证页面裸渲染，其他页面包裹 AppLayout（侧边栏+头部） -->
    <AppLayout v-if="!isAuthPage">
      <router-view />
    </AppLayout>
    <router-view v-else />
  </template>
</template>

<style scoped>
.app-loading {
  min-height: 100vh;
  background: var(--app-gradient);
}
</style>
