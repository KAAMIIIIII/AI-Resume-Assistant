<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useResumeStore } from '@/stores/resume'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/api'
import type { AnalysisRecord } from '@/api'
import { formatBeijingDate } from '@/utils/time'

const router = useRouter()
const resumeStore = useResumeStore()
const authStore = useAuthStore()
const loading = ref(true)

// 用户所有分析记录（用于统计卡和快速跳转）
const analyses = ref<AnalysisRecord[]>([])

// PDF 预览对话框状态
const pdfVisible = ref(false)
const pdfUrl = ref('')
const pdfTitle = ref('')

// 计算最高分记录，点击可跳转查看
const highestAnalysis = computed(() => {
  if (analyses.value.length === 0) return null
  return analyses.value.reduce((best, a) => a.overall_score > best.overall_score ? a : best)
})

const highestScore = computed(() => highestAnalysis.value?.overall_score ?? 0)

async function fetchAnalyses() {
  try {
    const res = await api.get('/analysis/')
    analyses.value = res.data
  } catch { /* ignore */ }
}

onMounted(async () => {
  // 并行加载用户信息、简历列表和分析记录
  await authStore.fetchUser()
  await resumeStore.fetchResumes()
  await fetchAnalyses()
  loading.value = false
})

function goUpload() {
  router.push('/upload')
}

function goAnalysis(id: number) {
  router.push(`/analysis/${id}`)
}

function goBestAnalysis() {
  if (highestAnalysis.value) {
    // 跳到最佳分析的简历页面，通过 ?aid= 指定查看哪条记录
    router.push(`/analysis/${highestAnalysis.value.resume_id}?aid=${highestAnalysis.value.id}`)
  }
}

async function handleDelete(id: number) {
  await resumeStore.deleteResume(id)
  // 删除后刷新分析计数
  await fetchAnalyses()
}

// 通过后端静态文件服务预览 PDF
function viewResume(row: { file_path: string; title: string }) {
  const filename = row.file_path.split(/[\\/]/).pop()
  pdfUrl.value = `/uploads/${filename}`
  pdfTitle.value = row.title
  pdfVisible.value = true
}
</script>

<template>
  <div class="page-container">
    <div class="welcome-section">
      <div class="welcome-text">
        <h2 v-if="authStore.user">你好，{{ authStore.user.username }}</h2>
        <p>智能分析简历，精准匹配岗位需求</p>
      </div>
      <el-button type="primary" size="large" @click="goUpload">
        <span style="margin-right: 4px">+</span> 上传简历
      </el-button>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-number">{{ resumeStore.resumes.length }}</div>
        <div class="stat-label">简历总数</div>
      </div>
      <div class="stat-card clickable" @click="goBestAnalysis">
        <div class="stat-number score">{{ highestScore }}</div>
        <div class="stat-label">最高得分</div>
      </div>
      <div class="stat-card clickable" @click="router.push('/history')">
        <div class="stat-number">{{ analyses.length }}</div>
        <div class="stat-label">分析记录</div>
      </div>
    </div>

    <div class="section">
      <h3 class="card-title">我的简历</h3>
      <el-table v-loading="loading" :data="resumeStore.resumes" style="width: 100%" empty-text="暂无简历，点击上方按钮上传">
        <el-table-column prop="title" label="简历名称" min-width="200" />
        <el-table-column prop="original_filename" label="原始文件" min-width="200" />
        <el-table-column label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatBeijingDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="360" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="viewResume(row)">
              查看
            </el-button>
            <el-button size="small" type="primary" link @click="goAnalysis(row.id)">
              查看分析
            </el-button>
            <el-button size="small" type="danger" link @click="handleDelete(row.id)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="pdfVisible" :title="pdfTitle" width="80%" top="30px" destroy-on-close>
      <iframe :src="pdfUrl" style="width: 100%; height: 75vh; border: none" />
    </el-dialog>
  </div>
</template>

<style scoped>
.welcome-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 32px 40px;
  color: #fff;
  margin-bottom: 24px;
}

.welcome-text h2 {
  font-size: 24px;
  margin-bottom: 8px;
}

.welcome-text p {
  opacity: 0.85;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  background: #fff;
  border-radius: 10px;
  padding: 24px;
  text-align: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.2s;
}

.stat-card.clickable {
  cursor: pointer;
}

.stat-card.clickable:hover {
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.2);
}

.stat-number {
  font-size: 32px;
  font-weight: 700;
  color: #667eea;
}

.stat-number.score {
  color: #67c23a;
}

.stat-label {
  color: #888;
  margin-top: 4px;
  font-size: 14px;
}

.section {
  background: #fff;
  border-radius: 10px;
  padding: 24px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}
</style>
