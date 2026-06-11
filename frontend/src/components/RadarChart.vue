<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'

interface RadarItem {
  name: string
  value: number
}

const props = defineProps<{
  data: RadarItem[]  // [{name: '技能匹配', value: 85}, ...]
}>()

const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

// 渲染 ECharts 雷达图：6 维度评分可视化
function renderChart() {
  if (!chartRef.value || props.data.length === 0) return

  // 复用实例，避免重复 init
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  // setOption 第二个参数 true = notMerge，数据变化时完全替换配置
  chartInstance.setOption(
    {
      tooltip: {
        trigger: 'item',
      },
      radar: {
        center: ['50%', '50%'],
        radius: '65%',
        // indicator: 6 个维度的名称和满分值
        indicator: props.data.map((item) => ({
          name: item.name,
          max: 100,
        })),
        axisName: {
          color: '#666',
          fontSize: 12,
        },
        splitArea: {
          areaStyle: {
            // 交替着色背景环
            color: ['rgba(102, 126, 234, 0.05)', 'rgba(102, 126, 234, 0.1)'],
          },
        },
      },
      series: [
        {
          type: 'radar',
          data: [
            {
              value: props.data.map((item) => item.value),
              name: '匹配度',
              areaStyle: {
                color: 'rgba(102, 126, 234, 0.25)',
              },
              lineStyle: {
                color: '#667eea',
                width: 2,
              },
              itemStyle: {
                color: '#667eea',
              },
            },
          ],
        },
      ],
    },
    true  // notMerge: 数据完全替换而非合并
  )
}

onMounted(renderChart)
// 深度监听数据变化，自动重新渲染图表
watch(() => props.data, renderChart, { deep: true })
</script>

<template>
  <div ref="chartRef" class="radar-chart"></div>
</template>

<style scoped>
.radar-chart {
  width: 100%;
  height: 400px;
}
</style>
