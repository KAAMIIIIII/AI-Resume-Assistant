import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

import App from './App.vue'
import router from './router'
import './styles/global.scss'

const app = createApp(App)

// Pinia — 全局状态管理（auth、resume 两个 store）
app.use(createPinia())
// Vue Router — 6 个路由，带导航守卫做登录拦截
app.use(router)
// Element Plus — 组件库，已配置 unplugin 自动导入
app.use(ElementPlus)
app.mount('#app')
