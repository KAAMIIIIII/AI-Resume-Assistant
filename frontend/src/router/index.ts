import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录' },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { title: '注册' },
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '首页', requiresAuth: true },
  },
  {
    path: '/upload',
    name: 'UploadResume',
    component: () => import('@/views/UploadResume.vue'),
    meta: { title: '上传简历', requiresAuth: true },
  },
  {
    path: '/analysis/:id',
    name: 'AnalysisReport',
    component: () => import('@/views/AnalysisReport.vue'),
    meta: { title: '分析报告', requiresAuth: true },
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('@/views/History.vue'),
    meta: { title: '历史记录', requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 全局导航守卫：设置页面标题 + 未登录拦截
router.beforeEach((to, _from, next) => {
  document.title = `${to.meta.title} - AI 简历诊断`
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
