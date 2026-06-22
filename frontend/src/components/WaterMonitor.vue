<template>
  <div class="monitor-card" :class="{ 'health-warning': isWarning }">
    <div class="card-header">
      <h2>🌊 海洋牧场水质监控</h2>
      <div class="selector">
        <label for="box-select">选择网箱：</label>
        <select id="box-select" v-model="selectedBox" @change="onBoxChange">
          <option value="" disabled>-- 请选择 --</option>
          <option v-for="box in boxes" :key="box.box_id" :value="box.box_id">
            {{ box.box_id }}
          </option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="waterData.length" class="chart-area">
      <v-chart :option="chartOption" autoresize style="height: 480px" />
      <div class="legend-info">
        <span class="legend-item">
          <span class="dot" style="background: #5470c6"></span> 溶解氧 (mg/L)
        </span>
        <span class="legend-item">
          <span class="dot" style="background: #91cc75"></span> 温度 (°C)
        </span>
        <span class="legend-item">
          <span class="dot" style="background: #fac858"></span> 盐度 (‰)
        </span>
        <span class="legend-item">
          <span class="dot" style="background: #ee6666"></span> 水质健康指数
        </span>
        <span class="legend-item warning-hint">
          ⚠️ 健康指数 &lt; 60 时背景变红预警
        </span>
      </div>
    </div>
    <div v-else class="empty">请选择一个网箱查看水质数据</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  MarkLineComponent,
  VisualMapComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { fetchBoxes, fetchWaterData } from '@/api'
import type { BoxItem, WaterData } from '@/api/types'

use([
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  MarkLineComponent,
  VisualMapComponent,
  CanvasRenderer,
])

const boxes = ref<BoxItem[]>([])
const selectedBox = ref('')
const waterData = ref<WaterData[]>([])
const loading = ref(false)
const error = ref('')

fetchBoxes()
  .then((d) => (boxes.value = d))
  .catch(() => (error.value = '获取网箱列表失败'))

const isWarning = computed(() => {
  if (!waterData.value.length) return false
  const latest = waterData.value[waterData.value.length - 1]
  return latest.health_index < 60
})

async function onBoxChange() {
  if (!selectedBox.value) return
  loading.value = true
  error.value = ''
  try {
    waterData.value = await fetchWaterData(selectedBox.value)
  } catch {
    error.value = '获取水质数据失败'
    waterData.value = []
  } finally {
    loading.value = false
  }
}

const chartOption = computed(() => {
  if (!waterData.value.length) return {}

  const times = waterData.value.map((d) => {
    const t = new Date(d.timestamp)
    return `${t.getHours().toString().padStart(2, '0')}:${t.getMinutes().toString().padStart(2, '0')}`
  })
  const doSeries = waterData.value.map((d) => d.dissolved_oxygen)
  const tempSeries = waterData.value.map((d) => d.temperature)
  const salSeries = waterData.value.map((d) => d.salinity)
  const healthSeries = waterData.value.map((d) => d.health_index)

  return {
    tooltip: { trigger: 'axis' },
    legend: {
      data: ['溶解氧', '温度', '盐度', '健康指数'],
      top: 0,
    },
    grid: { left: 60, right: 60, top: 50, bottom: 30 },
    xAxis: { type: 'category', data: times, boundaryGap: false },
    yAxis: [
      {
        type: 'value',
        name: '溶解氧/温度/盐度',
        position: 'left',
      },
      {
        type: 'value',
        name: '健康指数',
        position: 'right',
        min: 0,
        max: 100,
      },
    ],
    visualMap: {
      show: false,
      dimension: 0,
      pieces: waterData.value.map((d, i) => ({
        min: i,
        max: i,
        itemStyle: d.health_index < 60 ? { color: '#ff4d4f' } : {},
      })),
      seriesIndex: 3,
    },
    series: [
      {
        name: '溶解氧',
        type: 'line',
        data: doSeries,
        smooth: true,
        itemStyle: { color: '#5470c6' },
      },
      {
        name: '温度',
        type: 'line',
        data: tempSeries,
        smooth: true,
        itemStyle: { color: '#91cc75' },
      },
      {
        name: '盐度',
        type: 'line',
        data: salSeries,
        smooth: true,
        itemStyle: { color: '#fac858' },
      },
      {
        name: '健康指数',
        type: 'line',
        yAxisIndex: 1,
        data: healthSeries,
        smooth: true,
        itemStyle: { color: '#ee6666' },
        markLine: {
          silent: true,
          lineStyle: { color: '#ff4d4f', type: 'dashed' },
          data: [{ yAxis: 60, label: { formatter: '预警线 60' } }],
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(238,102,102,0.25)' },
              { offset: 1, color: 'rgba(238,102,102,0.02)' },
            ],
          },
        },
      },
    ],
  }
})
</script>

<style scoped>
.monitor-card {
  max-width: 960px;
  margin: 32px auto;
  padding: 24px 32px;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: background 0.4s, box-shadow 0.4s;
}

.monitor-card.health-warning {
  background: #fff1f0;
  box-shadow: 0 0 24px rgba(255, 77, 79, 0.35);
  border: 2px solid #ff4d4f;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.card-header h2 {
  margin: 0;
  font-size: 22px;
  color: #1a1a2e;
}

.selector label {
  font-weight: 500;
  margin-right: 8px;
}

.selector select {
  padding: 6px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  outline: none;
  transition: border-color 0.2s;
}

.selector select:focus {
  border-color: #4096ff;
}

.loading,
.empty,
.error {
  text-align: center;
  padding: 48px 0;
  color: #888;
  font-size: 15px;
}

.error {
  color: #ff4d4f;
}

.legend-info {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  padding: 8px 0 0;
  font-size: 13px;
  color: #555;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.warning-hint {
  color: #ff4d4f;
  font-weight: 500;
}
</style>
