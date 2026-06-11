<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { computed } from 'vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// 根据当前路径计算侧边栏高亮菜单项
const activeMenu = computed(() => {
  const path = route.path
  if (path === '/') return '/'
  if (path.startsWith('/upload')) return '/upload'
  if (path.startsWith('/history')) return '/history'
  return '/'
})

function logout() {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <div class="app-layout">
    <aside class="sidebar">
      <div class="sidebar-logo" @click="router.push('/')">
        <span class="logo-icon">AI</span>
        <span class="logo-text">简历诊断</span>
      </div>

      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        background-color="#1e1e2d"
        text-color="#a2a3b7"
        active-text-color="#fff"
        @select="(key: string) => router.push(key)"
      >
        <el-menu-item index="/">
          <span>📊 首页</span>
        </el-menu-item>
        <el-menu-item index="/upload">
          <span>📄 上传简历</span>
        </el-menu-item>
        <el-menu-item index="/history">
          <span>📋 历史记录</span>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-footer">
        <div class="user-info" v-if="authStore.user">
          <el-avatar :size="32">{{ authStore.user.username.charAt(0).toUpperCase() }}</el-avatar>
          <span class="username">{{ authStore.user.username }}</span>
        </div>
        <el-button text class="logout-btn" @click="logout">退出登录</el-button>
      </div>
    </aside>

    <main class="main-content">
      <slot />
    </main>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
}

.sidebar {
  position: sticky;
  top: 0;
  width: 240px;
  height: 100vh;
  background: #1e1e2d;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 24px;
  cursor: pointer;
}

.logo-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  font-size: 16px;
}

.logo-text {
  color: #fff;
  font-size: 18px;
  font-weight: 600;
}

.sidebar-menu {
  border-right: none;
  flex: 1;
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid #2d2d3f;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #a2a3b7;
  font-size: 14px;
}

.logout-btn {
  color: #a2a3b7 !important;
  font-size: 13px;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  background: #f5f7fa;
}
</style>
