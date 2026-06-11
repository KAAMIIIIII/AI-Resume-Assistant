import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api'
import type { Resume, AnalysisRecord } from '@/api'

export const useResumeStore = defineStore('resume', () => {
  // 简历列表（Dashboard 表格）
  const resumes = ref<Resume[]>([])
  // 当前查看的简历
  const currentResume = ref<Resume | null>(null)
  // 当前查看的分析结果
  const currentAnalysis = ref<AnalysisRecord | null>(null)

  async function fetchResumes() {
    const res = await api.get('/resumes/')
    resumes.value = res.data
  }

  async function uploadResume(title: string, file: File) {
    // 使用 FormData 上传文件（axios 会自动设置 multipart/form-data）
    const formData = new FormData()
    formData.append('title', title)
    formData.append('file', file)
    const res = await api.post('/resumes/upload', formData)
    // 新简历插入列表最前面
    resumes.value.unshift(res.data)
    return res.data
  }

  async function fetchResume(id: number) {
    const res = await api.get(`/resumes/${id}`)
    currentResume.value = res.data
    return res.data
  }

  async function deleteResume(id: number) {
    await api.delete(`/resumes/${id}`)
    resumes.value = resumes.value.filter((r) => r.id !== id)
  }

  return {
    resumes,
    currentResume,
    currentAnalysis,
    fetchResumes,
    uploadResume,
    fetchResume,
    deleteResume,
  }
})
