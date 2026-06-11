import axios from 'axios'
import { ElMessage } from 'element-plus'

const baseURL = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL}/api`
  : '/api'

export const api = axios.create({
  baseURL,
  timeout: 30000,
})

// 请求拦截器：自动附加 JWT Bearer 令牌
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：统一错误提示 + 401 自动跳转登录页
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const msg = error.response?.data?.detail || '请求失败，请重试'
    ElMessage.error(msg)
    // 非认证接口的 401 视为令牌过期，清除 token 并跳转登录
    if (error.response?.status === 401 && !error.config.url?.includes('/auth/')) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// ----- 共享 TypeScript 接口（前后端约定） -----

export interface User {
  id: number
  email: string
  username: string
  role: string
  created_at: string
}

export interface Resume {
  id: number
  user_id: number
  title: string
  original_filename: string
  file_path: string
  parsed_content: string
  structured_data: Record<string, any>
  version: number
  created_at: string
  updated_at: string
}

export interface AnalysisRecord {
  id: number
  user_id: number
  resume_id: number
  resume_title: string
  job_description: string
  overall_score: number
  // 6 维度分项评分
  category_scores: Record<string, number>
  // 包含 strengths, weaknesses, gap_analysis, category_weights
  details: Record<string, any>
  // 优化建议列表
  suggestions: Array<{
    priority: string
    category: string
    suggestion: string
  }>
  raw_report: string
  created_at: string
}
