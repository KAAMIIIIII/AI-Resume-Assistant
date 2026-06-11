<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import { api } from '@/api'
import type { AnalysisRecord } from '@/api'
import { formatBeijingTime } from '@/utils/time'

const router = useRouter()
const loading = ref(false)
const analyses = ref<AnalysisRecord[]>([])

// 多选对比：勾选的行 ID 数组
const compareIds = ref<number[]>([])
const compareDialogVisible = ref(false)
const compareData = ref<any>(null)

const categoryLabels: Record<string, string> = {
  skills: '技能匹配',
  experience: '经验匹配',
  education: '学历匹配',
  projects: '项目经验',
  language: '语言能力',
  certificates: '证书资质',
}

// ---- 自定义浮动 Tooltip ----
// 原理：cell-mouse-enter 时记录行数据，400ms 防抖后通过 Teleport 渲染到 body
const tooltipVisible = ref(false)
const tooltipText = ref('')
const tooltipX = ref(0)
const tooltipY = ref(0)
const hoverRow = ref<AnalysisRecord | null>(null)
let hoverTimer: ReturnType<typeof setTimeout> | null = null

function resetTooltipTimer() {
  if (hoverTimer) clearTimeout(hoverTimer)
  tooltipVisible.value = false
  hoverTimer = setTimeout(() => {
    if (hoverRow.value) {
      tooltipText.value = hoverRow.value.resume_title || '（无标题）'
      tooltipVisible.value = true
    }
  }, 400)  // 400ms 防抖：鼠标静止后才显示
}

function clearTooltipTimer() {
  if (hoverTimer) {
    clearTimeout(hoverTimer)
    hoverTimer = null
  }
  tooltipVisible.value = false
}

function onCellEnter(row: AnalysisRecord, _col: any, _cell: any, event: MouseEvent) {
  hoverRow.value = row
  tooltipX.value = event.clientX
  tooltipY.value = event.clientY
  resetTooltipTimer()
}

function onCellLeave() {
  hoverRow.value = null
  clearTooltipTimer()
}

function onSectionMouseMove(event: MouseEvent) {
  // 更新 tooltip 位置，重置防抖计时器
  tooltipX.value = event.clientX
  tooltipY.value = event.clientY
  if (hoverRow.value) {
    resetTooltipTimer()
  }
}

onUnmounted(() => {
  clearTooltipTimer()
})

onMounted(async () => {
  loading.value = true
  try {
    const res = await api.get('/analysis/')
    analyses.value = res.data
  } finally {
    loading.value = false
  }
})

function goAnalysis(row: AnalysisRecord) {
  router.push(`/analysis/${row.resume_id}?aid=${row.id}`)
}

async function doCompare() {
  if (compareIds.value.length < 2) return
  try {
    const res = await api.post('/analysis/compare', {
      analysis_ids: compareIds.value,
    })
    compareData.value = res.data
    compareDialogVisible.value = true
  } catch {}
}

async function handleDelete() {
  if (compareIds.value.length === 0) return
  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${compareIds.value.length} 条分析记录吗？`,
      '删除确认',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    for (const id of compareIds.value) {
      await api.delete(`/analysis/${id}`)
    }
    // 从本地列表移除已删除项
    analyses.value = analyses.value.filter(a => !compareIds.value.includes(a.id))
    compareIds.value = []
    ElMessage.success('删除成功')
  } catch { /* 用户取消 */ }
}

function goCompareAnalysis(item: any) {
  compareDialogVisible.value = false
  router.push(`/analysis/${item.resume_id}?aid=${item.id}`)
}

// 在对比弹窗中为每个分析渲染横向条形图
function initCompareCharts() {
  if (!compareData.value) return
  const containers = document.querySelectorAll<HTMLElement>('.compare-chart')
  containers.forEach((el) => {
    const analysisId = el.dataset.aid
    const item = compareData.value.analyses.find((a: any) => a.id === Number(analysisId))
    if (!item) return
    const scores = item.category_scores || {}
    const cats = Object.keys(scores)
    const chart = echarts.init(el)
    chart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 100, right: 20, top: 8, bottom: 8 },
      xAxis: { type: 'value', max: 100, axisLabel: { fontSize: 10 } },
      yAxis: {
        type: 'category',
        data: cats.map((k: string) => categoryLabels[k] || k),
        axisLabel: { fontSize: 11, color: '#666' },
      },
      series: [{
        type: 'bar',
        data: cats.map((k: string) => scores[k]),
        itemStyle: {
          // 根据分数着色：>=80 绿，>=60 橙，<60 红
          color: (params: any) => {
            const v = params.value as number
            if (v >= 80) return '#67c23a'
            if (v >= 60) return '#e6a23c'
            return '#f56c6c'
          },
          borderRadius: [0, 4, 4, 0],
        },
        barMaxWidth: 20,
      }],
    })
  })
}

// 监听弹窗打开，等 DOM 渲染后初始化图表
watch(compareDialogVisible, async (visible) => {
  if (visible) {
    await nextTick()
    initCompareCharts()
  }
})
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <el-button link @click="router.push('/')">&lt; 返回首页</el-button>
    </div>

    <div class="section" @mousemove="onSectionMouseMove">
      <div class="section-header">
        <h3 class="card-title">历史分析记录</h3>
        <div class="header-actions">
          <el-button
            type="danger"
            :disabled="compareIds.length === 0"
            @click="handleDelete"
          >
            删除 ({{ compareIds.length }})
          </el-button>
          <el-button
            type="warning"
            :disabled="compareIds.length < 2"
            @click="doCompare"
          >
            版本对比 ({{ compareIds.length }})
          </el-button>
        </div>
      </div>

      <el-table
        v-loading="loading"
        :data="analyses"
        style="width: 100%"
        empty-text="暂无分析记录"
        @selection-change="(rows: AnalysisRecord[]) => (compareIds = rows.map(r => r.id))"
        @cell-mouse-enter="onCellEnter"
        @cell-mouse-leave="onCellLeave"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column label="分析时间" width="180">
          <template #default="{ row }">
            {{ formatBeijingTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="综合评分" width="120">
          <template #default="{ row }">
            <el-tag
              :type="row.overall_score >= 80 ? 'success' : row.overall_score >= 60 ? 'warning' : 'danger'"
              size="large"
            >
              {{ row.overall_score }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="job_description" label="JD 摘要" min-width="300">
          <template #default="{ row }">
            {{ row.job_description.slice(0, 80) }}{{ row.job_description.length > 80 ? '...' : '' }}
          </template>
        </el-table-column>
        <el-table-column label="各维度评分" min-width="300">
          <template #default="{ row }">
            <div class="score-tags" v-if="row.category_scores">
              <el-tag
                v-for="(score, key) in row.category_scores"
                :key="key"
                size="small"
                :type="(score as number) >= 80 ? 'success' : (score as number) >= 60 ? 'warning' : 'danger'"
              >
                {{ categoryLabels[key] || key }}: {{ score }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="goAnalysis(row)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 自定义浮动 Tooltip -->
      <Teleport to="body">
        <transition name="tooltip-fade">
          <div
            v-if="tooltipVisible"
            class="row-tooltip"
            :style="{ left: tooltipX + 14 + 'px', top: tooltipY - 10 + 'px' }"
          >
            {{ tooltipText }}
          </div>
        </transition>
      </Teleport>
    </div>

    <!-- 版本对比弹窗 -->
    <el-dialog v-model="compareDialogVisible" title="版本对比" width="900px">
      <div v-if="compareData" class="compare-grid">
        <div
          v-for="item in compareData.analyses"
          :key="item.id"
          class="compare-card"
          @click="goCompareAnalysis(item)"
        >
          <h4>{{ formatBeijingTime(item.created_at) }}</h4>
          <div class="compare-score">{{ item.overall_score }}</div>
          <div class="compare-chart" :data-aid="item.id"></div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.page-header {
  margin-bottom: 24px;
}

.section {
  background: #fff;
  border-radius: 10px;
  padding: 24px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.score-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.compare-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
  gap: 16px;
}

.compare-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: box-shadow 0.2s, border-color 0.2s;
}

.compare-card:hover {
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.18);
  border-color: #667eea;
}

.compare-card h4 {
  margin-bottom: 8px;
  font-size: 14px;
  color: #888;
}

.compare-score {
  font-size: 48px;
  font-weight: 700;
  color: #667eea;
  text-align: center;
  margin: 16px 0;
}

.compare-chart {
  width: 100%;
  height: 200px;
  margin-top: 16px;
}

</style>

<style>
/* ---- 自定义浮动 tooltip（非 scoped，因为通过 Teleport 挂载到 body） ---- */
.row-tooltip {
  position: fixed;
  z-index: 9999;
  max-width: 320px;
  padding: 8px 16px;
  background: rgba(31, 41, 55, 0.92);
  backdrop-filter: blur(8px);
  color: #f9fafb;
  font-size: 13px;
  line-height: 1.5;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.18);
  pointer-events: none;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tooltip-fade-enter-active,
.tooltip-fade-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.tooltip-fade-enter-from,
.tooltip-fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}
</style>
