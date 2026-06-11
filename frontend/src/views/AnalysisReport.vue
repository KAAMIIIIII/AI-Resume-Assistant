<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useResumeStore } from '@/stores/resume'
import { api } from '@/api'
import type { AnalysisRecord } from '@/api'
import { formatBeijingTime } from '@/utils/time'
import RadarChart from '@/components/RadarChart.vue'
import ScoreCard from '@/components/ScoreCard.vue'

const route = useRoute()
const router = useRouter()
const resumeStore = useResumeStore()

const resumeId = Number(route.params.id)
const loading = ref(false)
const analyzing = ref(false)
const analyses = ref<AnalysisRecord[]>([])          // 该简历的所有历史分析
const currentAnalysis = ref<AnalysisRecord | null>(null)  // 当前选中的分析

const jdText = ref('')                        // 岗位描述输入
const streamText = ref('')                    // 流式显示的自然语言报告（仅报告部分）
const isParsingJSON = ref(false)              // 是否已进入 JSON 接收阶段

const JSON_DELIMITER = '<!--JSON-->'

onMounted(async () => {
  loading.value = true
  try {
    await resumeStore.fetchResume(resumeId)
    // 加载该简历的历史分析记录
    const res = await api.get('/analysis/', { params: { resume_id: resumeId } })
    analyses.value = res.data
    // URL 参数 ?aid= 指定查看的历史记录
    const targetAid = Number(route.query.aid)
    if (targetAid) {
      const found = analyses.value.find(a => a.id === targetAid)
      currentAnalysis.value = found || null
    }
    // 默认展示最新一条
    if (!currentAnalysis.value && analyses.value.length > 0) {
      currentAnalysis.value = analyses.value[0]
    }
  } finally {
    loading.value = false
  }
})

async function startAnalysis() {
  if (!jdText.value.trim()) return
  analyzing.value = true
  streamText.value = ''
  isParsingJSON.value = false

  try {
    // 使用原生 fetch（而非 axios），因为需要读取 SSE 流式响应
    const baseURL = import.meta.env.VITE_API_BASE_URL || ''
    const response = await fetch(`${baseURL}/api/analysis/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${localStorage.getItem('token')}`,
      },
      body: JSON.stringify({
        resume_id: resumeId,
        job_description: jdText.value,
      }),
    })

    // ReadableStream 逐块读取 SSE 数据
    const reader = response.body?.getReader()
    if (!reader) return

    const decoder = new TextDecoder()
    let buffer = ''  // 缓冲区：处理跨 chunk 的不完整行

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''  // 最后一个可能是不完整的行，留到下一次

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const data = JSON.parse(line.slice(6))  // 去掉 "data: " 前缀
          if (data.error) {
            throw new Error(data.error)
          }
          if (data.done) {
            // 分析完成：拉取完整的 AnalysisRecord 并更新列表
            const res = await api.get(`/analysis/${data.analysis_id}`)
            currentAnalysis.value = res.data
            analyses.value.unshift(res.data)
          } else if (data.chunk) {
            // 流式文本片段：在检测到 <!--JSON--> 之前显示给用户
            if (!isParsingJSON.value) {
              streamText.value += data.chunk
              const idx = streamText.value.indexOf(JSON_DELIMITER)
              if (idx !== -1) {
                // 截断分隔标记及之后的内容，只保留自然语言报告
                streamText.value = streamText.value.slice(0, idx).trimEnd()
                isParsingJSON.value = true
              }
            }
            // 标记后静默接收 JSON 数据，不显示到界面
          }
        } catch { /* 忽略格式异常的 SSE 行 */ }
      }
    }
  } catch (e: any) {
    ElMessage.error(e.message || 'AI 分析请求失败，请检查后端日志')
  } finally {
    analyzing.value = false
  }
}

// 雷达图数据：6 个维度分数 → {name, value}[]
const radarData = computed(() => {
  if (!currentAnalysis.value?.category_scores) return []
  const labels: Record<string, string> = {
    skills: '技能匹配',
    experience: '经验匹配',
    education: '学历匹配',
    projects: '项目经验',
    language: '语言能力',
    certificates: '证书资质',
  }
  return Object.entries(currentAnalysis.value.category_scores).map(([key, val]) => ({
    name: labels[key] || key,
    value: val,
  }))
})

// AI 判定的维度权重（0~1 之间）
const weights = computed(() => {
  return currentAnalysis.value?.details?.category_weights || {}
})

const weightLabels: Record<string, string> = {
  skills: '技能',
  experience: '经验',
  education: '学历',
  projects: '项目',
  language: '语言',
  certificates: '证书',
}

const priorityLabels: Record<string, string> = {
  high: '高',
  medium: '中',
  low: '低',
}

const categoryLabels: Record<string, string> = {
  skills: '技能匹配',
  experience: '经验匹配',
  education: '学历匹配',
  projects: '项目经验',
  language: '语言能力',
  certificates: '证书资质',
}

// 将建议的英文 key 映射为中文标签
const formattedSuggestions = computed(() => {
  return currentAnalysis.value?.suggestions?.map((s) => ({
    ...s,
    priorityLabel: priorityLabels[s.priority] || s.priority,
    categoryLabel: categoryLabels[s.category] || s.category,
  })) || []
})

const pdfVisible = ref(false)
const pdfUrl = ref('')
const pdfTitle = ref('')

function viewResume() {
  const resume = resumeStore.currentResume
  if (!resume) return
  const filename = resume.file_path.split(/[\\/]/).pop()
  pdfUrl.value = `/uploads/${filename}`
  pdfTitle.value = resume.title
  pdfVisible.value = true
}

// 综合评分颜色：>=80 绿色，>=60 橙色，<60 红色
const scoreColor = computed(() => {
  const s = currentAnalysis.value?.overall_score ?? 0
  if (s >= 80) return '#67c23a'
  if (s >= 60) return '#e6a23c'
  return '#f56c6c'
})
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <el-button link @click="router.push('/')">
        &lt; 返回首页
      </el-button>
      <div class="header-row">
        <h2 v-if="resumeStore.currentResume">
          {{ resumeStore.currentResume.title }} - 分析报告
        </h2>
        <el-button v-if="resumeStore.currentResume" type="primary" size="small" @click="viewResume">
          查看简历
        </el-button>
      </div>
    </div>

    <!-- 输入 JD -->
    <div class="jd-section">
      <h3 class="card-title">输入岗位 JD</h3>
      <el-input
        v-model="jdText"
        type="textarea"
        :rows="5"
        placeholder="请粘贴完整的岗位描述（JD），AI 将根据 JD 要求进行精准分析..."
      />
      <el-button
        type="primary"
        size="large"
        :loading="analyzing"
        :disabled="!jdText.trim()"
        class="analyze-btn"
        @click="startAnalysis"
      >
        {{ analyzing ? 'AI 分析中...' : '开始 AI 分析' }}
      </el-button>
    </div>

    <!-- 流式报告：ChatGPT 风格对话气泡 -->
    <div v-if="analyzing && streamText" class="stream-report">
      <div class="chat-bubble">
        <div class="chat-avatar">AI</div>
        <div class="chat-content">
          <p class="chat-text">{{ streamText }}<span class="cursor-blink">|</span></p>
        </div>
      </div>
    </div>

    <!-- 正在解析 JSON，生成结构化报告 -->
    <div v-if="analyzing && isParsingJSON && streamText" class="parsing-hint">
      <el-alert type="info" :closable="false" center>
        <template #title>
          <span class="parsing-pulse">正在生成结构化分析报告...</span>
        </template>
      </el-alert>
    </div>

    <!-- 分析结果 -->
    <div v-if="currentAnalysis && !analyzing" class="result-section" v-loading="loading">
      <!-- 综合评分 -->
      <div class="overall-score">
        <ScoreCard
          :score="currentAnalysis.overall_score"
          :color="scoreColor"
          label="综合匹配度"
        />
      </div>

      <!-- 雷达图 + 详情 -->
      <div class="report-grid">
        <div class="radar-box">
          <RadarChart :data="radarData" />
        </div>
        <div class="details-box">
          <!-- 维度权重 -->
          <div v-if="Object.keys(weights).length" class="detail-block">
            <h4>📐 维度权重（AI 根据 JD 判定）</h4>
            <div class="weight-tags">
              <el-tag
                v-for="(w, key) in weights"
                :key="key"
                :type="(w as number) >= 0.2 ? 'danger' : (w as number) >= 0.1 ? 'warning' : 'info'"
                size="large"
              >
                {{ weightLabels[String(key)] || key }}: {{ ((w as number) * 100).toFixed(0) }}%
              </el-tag>
            </div>
          </div>

          <div v-if="currentAnalysis.details?.strengths?.length" class="detail-block">
            <h4>✅ 优势</h4>
            <ul>
              <li v-for="(item, i) in currentAnalysis.details.strengths" :key="i">
                {{ item }}
              </li>
            </ul>
          </div>
          <div v-if="currentAnalysis.details?.weaknesses?.length" class="detail-block">
            <h4>⚠️ 待提升</h4>
            <ul>
              <li v-for="(item, i) in currentAnalysis.details.weaknesses" :key="i">
                {{ item }}
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- 优化建议 -->
      <div v-if="formattedSuggestions.length" class="suggestions-section">
        <h3 class="card-title">优化建议</h3>
        <el-timeline>
          <el-timeline-item
            v-for="(item, i) in formattedSuggestions"
            :key="i"
            :timestamp="`优先级: ${item.priorityLabel} | 分类: ${item.categoryLabel}`"
            placement="top"
            :color="item.priority === 'high' ? '#f56c6c' : item.priority === 'medium' ? '#e6a23c' : '#67c23a'"
          >
            <el-card>
              <p>{{ item.suggestion }}</p>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>

      <!-- 历史记录 -->
      <div v-if="analyses.length > 1" class="history-section">
        <h3 class="card-title">历史分析</h3>
        <el-table :data="analyses" style="width: 100%">
          <el-table-column label="时间" width="180">
            <template #default="{ row }">
              {{ formatBeijingTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="overall_score" label="综合评分" width="120">
            <template #default="{ row }">
              <el-tag :type="row.overall_score >= 80 ? 'success' : row.overall_score >= 60 ? 'warning' : 'danger'">
                {{ row.overall_score }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="job_description" label="JD 摘要" min-width="300">
            <template #default="{ row }">
              {{ row.job_description.slice(0, 80) }}{{ row.job_description.length > 80 ? '...' : '' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click="currentAnalysis = row">
                查看
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!currentAnalysis && !analyzing && !loading" class="empty-state">
      <p>暂无分析记录，请在上方输入 JD 开始分析</p>
    </div>

    <el-dialog v-model="pdfVisible" :title="pdfTitle" width="80%" top="30px" destroy-on-close>
      <iframe :src="pdfUrl" style="width: 100%; height: 75vh; border: none" />
    </el-dialog>
  </div>
</template>

<style scoped>
.page-header {
  margin-bottom: 24px;
}

.header-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 8px;
}

.header-row h2 {
  margin: 0;
  font-size: 22px;
}

.jd-section {
  background: #fff;
  border-radius: 10px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.analyze-btn {
  margin-top: 16px;
}

/* ---- ChatGPT 风格流式气泡 ---- */
.stream-report {
  margin-bottom: 24px;
}

.chat-bubble {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.chat-avatar {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}

.chat-content {
  flex: 1;
  background: #fff;
  border-radius: 12px;
  padding: 20px 24px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  line-height: 1.8;
  min-height: 48px;
}

.chat-text {
  font-size: 15px;
  color: #333;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}

.cursor-blink {
  color: #667eea;
  font-weight: 700;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* ---- 解析提示 ---- */
.parsing-hint {
  margin-bottom: 24px;
}

.parsing-pulse {
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ---- 报告结果（不变） ---- */
.overall-score {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

.report-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.radar-box {
  background: #fff;
  border-radius: 10px;
  padding: 24px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.details-box {
  background: #fff;
  border-radius: 10px;
  padding: 24px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.detail-block {
  margin-bottom: 20px;
}

.detail-block h4 {
  font-size: 16px;
  margin-bottom: 8px;
}

.detail-block ul {
  padding-left: 20px;
}

.detail-block li {
  line-height: 1.8;
  color: #555;
}

.weight-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.suggestions-section {
  background: #fff;
  border-radius: 10px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.history-section {
  background: #fff;
  border-radius: 10px;
  padding: 24px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.empty-state {
  text-align: center;
  padding: 60px 0;
  color: #999;
}
</style>
