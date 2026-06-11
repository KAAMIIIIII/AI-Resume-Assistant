<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  score: number
  color: string    // 环形边框和数字颜色，由父组件根据分数计算
  label: string    // 评分项名称，如"综合匹配度"
}>()

// 根据分数判定等级
const level = computed(() => {
  if (props.score >= 80) return '优秀'
  if (props.score >= 60) return '良好'
  return '需优化'
})
</script>

<template>
  <div class="score-card">
    <!-- 圆环：通过 border 实现环形视觉效果 -->
    <div class="score-ring" :style="{ borderColor: color }">
      <div class="score-inner">
        <span class="score-number" :style="{ color }">{{ score }}</span>
        <span class="score-unit">分</span>
      </div>
    </div>
    <div class="score-label">{{ label }}</div>
    <el-tag :color="color" effect="dark" size="large">{{ level }}</el-tag>
  </div>
</template>

<style scoped>
.score-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.score-ring {
  width: 140px;
  height: 140px;
  border-radius: 50%;
  border: 6px solid;
  display: flex;
  align-items: center;
  justify-content: center;
}

.score-inner {
  text-align: center;
}

.score-number {
  font-size: 42px;
  font-weight: 700;
  line-height: 1;
}

.score-unit {
  font-size: 16px;
  color: #888;
  margin-left: 2px;
}

.score-label {
  font-size: 16px;
  color: #666;
  font-weight: 500;
}
</style>
