<template>
  <div class="monitor-card" :class="{ 'health-warning': isWarning }">
    <div class="card-header">
      <h2>🌊 海洋牧场水质监控</h2>
      <div class="header-right">
        <div class="selector">
          <label for="box-select">选择网箱：</label>
          <select
            id="box-select"
            v-model="selectedBox"
            @change="onBoxChange"
            :disabled="loading"
          >
            <option value="" disabled>-- 请选择 --</option>
            <option v-for="box in boxes" :key="box.box_id" :value="box.box_id">
              {{ box.box_id }}
            </option>
          </select>
        </div>
        <div class="patrol-toggle">
          <label class="switch">
            <input type="checkbox" v-model="patrolOn" @change="onPatrolToggle" />
            <span class="slider"></span>
          </label>
          <span class="patrol-label">{{ patrolOn ? '轮巡中' : '自动轮巡' }}</span>
          <span v-if="patrolOn" class="patrol-countdown">{{ countdown }}s</span>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="waterData.length" class="chart-area">
      <div v-if="hasMissingData" class="missing-hint">
        ⚠️ 部分数据点存在缺失指标（{{ missingStats }}），已自动跳过空值并在折线中断开显示
      </div>
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

    <Teleport to="body">
      <div v-if="alertVisible" class="alert-overlay" @click.self>
        <div class="alert-box">
          <div class="alert-icon">🚨</div>
          <div class="alert-title">水质健康指数持续报警</div>
          <div class="alert-body">
            网箱 <b>{{ alertBoxId }}</b> 的健康指数连续 3 次低于 60 分危险线！<br />
            当前指数：<b class="alert-score">{{ alertScores.join(' → ') }}</b><br />
            请立即排查溶解氧、温度、盐度是否异常！
          </div>
          <button class="alert-btn" @click="dismissAlert">我知道了</button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onErrorCaptured, onUnmounted } from 'vue'
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
const renderError = ref(false)

const patrolOn = ref(false)
let patrolTimer: ReturnType<typeof setInterval> | null = null
const countdown = ref(10)
let countdownTimer: ReturnType<typeof setInterval> | null = null

const alertVisible = ref(false)
const alertBoxId = ref('')
const alertScores = ref<number[]>([])

onErrorCaptured((e) => {
  console.error('组件渲染异常:', e)
  renderError.value = true
  error.value = '页面渲染异常，请刷新重试'
  return false
})

fetchBoxes()
  .then((d) => (boxes.value = d))
  .catch((e) => {
    console.error('获取网箱列表失败:', e)
    error.value = '获取网箱列表失败，请检查后端连接'
  })

onUnmounted(() => {
  stopPatrol()
})

function startPatrol() {
  if (boxes.value.length === 0) return
  countdown.value = 10

  countdownTimer = setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) countdown.value = 10
  }, 1000)

  patrolTimer = setInterval(() => {
    const idx = boxes.value.findIndex((b) => b.box_id === selectedBox.value)
    const nextIdx = (idx + 1) % boxes.value.length
    selectedBox.value = boxes.value[nextIdx].box_id
    onBoxChange()
    countdown.value = 10
  }, 10000)
}

function stopPatrol() {
  if (patrolTimer) {
    clearInterval(patrolTimer)
    patrolTimer = null
  }
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
}

function onPatrolToggle() {
  if (patrolOn.value) {
    if (selectedBox.value === '' && boxes.value.length > 0) {
      selectedBox.value = boxes.value[0].box_id
      onBoxChange()
    }
    startPatrol()
  } else {
    stopPatrol()
  }
}

const hasMissingData = computed(() => {
  return waterData.value.some(
    (d) =>
      d.dissolved_oxygen == null ||
      d.temperature == null ||
      d.salinity == null ||
      d.health_index == null,
  )
})

const missingStats = computed(() => {
  const total = waterData.value.length
  let doMiss = 0
  let tempMiss = 0
  let salMiss = 0
  let hiMiss = 0
  for (const d of waterData.value) {
    if (d.dissolved_oxygen == null) doMiss++
    if (d.temperature == null) tempMiss++
    if (d.salinity == null) salMiss++
    if (d.health_index == null) hiMiss++
  }
  const parts: string[] = []
  if (doMiss) parts.push(`溶解氧 ${doMiss}/${total}`)
  if (tempMiss) parts.push(`温度 ${tempMiss}/${total}`)
  if (salMiss) parts.push(`盐度 ${salMiss}/${total}`)
  if (hiMiss) parts.push(`健康指数 ${hiMiss}/${total}`)
  return parts.join('、')
})

const isWarning = computed(() => {
  if (!waterData.value.length) return false
  const latestWithIndex = [...waterData.value]
    .reverse()
    .find((d) => d.health_index != null)
  return latestWithIndex ? (latestWithIndex.health_index as number) < 60 : false
})

function checkConsecutiveLowHealth() {
  const validPoints = waterData.value
    .filter((d) => d.health_index != null)
    .map((d) => d.health_index as number)

  if (validPoints.length < 3) return

  const last3 = validPoints.slice(-3)
  if (last3.every((v) => v < 60)) {
    alertBoxId.value = selectedBox.value
    alertScores.value = last3
    alertVisible.value = true
  }
}

function dismissAlert() {
  alertVisible.value = false
}

async function onBoxChange() {
  if (!selectedBox.value) return
  loading.value = true
  error.value = ''
  renderError.value = false
  try {
    const data = await fetchWaterData(selectedBox.value)
    waterData.value = data.filter(
      (d) =>
        d.timestamp &&
        (d.dissolved_oxygen != null ||
          d.temperature != null ||
          d.salinity != null ||
          d.health_index != null),
    )
    if (waterData.value.length === 0) {
      error.value = '该网箱最近24小时的有效数据为空'
    } else {
      checkConsecutiveLowHealth()
    }
  } catch (e: any) {
    console.error('获取水质数据失败:', e)
    const detail = e?.response?.data?.detail || e?.message || '网络错误'
    error.value = `获取水质数据失败：${detail}`
    waterData.value = []
  } finally {
    loading.value = false
  }
}

const chartOption = computed(() => {
  if (!waterData.value.length || renderError.value) return {}

  const times = waterData.value.map((d) => {
    try {
      const t = new Date(d.timestamp)
      if (isNaN(t.getTime())) return ''
      const h = t.getHours().toString().padStart(2, '0')
      const m = t.getMinutes().toString().padStart(2, '0')
      return `${h}:${m}`
    } catch {
      return ''
    }
  })

  const doSeries = waterData.value.map((d) =>
    d.dissolved_oxygen != null ? Number(d.dissolved_oxygen) : null,
  )
  const tempSeries = waterData.value.map((d) =>
    d.temperature != null ? Number(d.temperature) : null,
  )
  const salSeries = waterData.value.map((d) =>
    d.salinity != null ? Number(d.salinity) : null,
  )
  const healthSeries = waterData.value.map((d) =>
    d.health_index != null ? Number(d.health_index) : null,
  )

  const validHealthIdx = healthSeries.findIndex((v) => v != null && v < 60)
  const isAnyWarning = validHealthIdx !== -1

  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        if (!Array.isArray(params) || !params.length) return ''
        const timeLabel = params[0].axisValue || ''
        const idx = params[0].dataIndex
        const item = waterData.value[idx]
        const parts = [`<b>${timeLabel}</b>`]
        const labelMap: Record<string, string> = {
          dissolved_oxygen: '溶解氧',
          temperature: '温度',
          salinity: '盐度',
          health_index: '健康指数',
        }
        const unitMap: Record<string, string> = {
          dissolved_oxygen: ' mg/L',
          temperature: ' °C',
          salinity: ' ‰',
          health_index: ' 分',
        }
        const keyMap = ['dissolved_oxygen', 'temperature', 'salinity', 'health_index']
        for (const k of keyMap) {
          const v = (item as any)[k]
          if (v == null) {
            parts.push(`${labelMap[k]}: <span style="color:#999">缺失</span>`)
          } else {
            parts.push(`${labelMap[k]}: ${v}${unitMap[k]}`)
          }
        }
        if (item?.missing_fields?.length) {
          parts.push(
            `<span style="color:#ff4d4f">缺失字段: ${item.missing_fields.join(', ')}</span>`,
          )
        }
        return parts.join('<br/>')
      },
    },
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
        itemStyle: d.health_index != null && d.health_index < 60
          ? { color: '#ff4d4f' }
          : {},
      })),
      seriesIndex: 3,
    },
    series: [
      {
        name: '溶解氧',
        type: 'line',
        data: doSeries,
        smooth: true,
        connectNulls: false,
        itemStyle: { color: '#5470c6' },
      },
      {
        name: '温度',
        type: 'line',
        data: tempSeries,
        smooth: true,
        connectNulls: false,
        itemStyle: { color: '#91cc75' },
      },
      {
        name: '盐度',
        type: 'line',
        data: salSeries,
        smooth: true,
        connectNulls: false,
        itemStyle: { color: '#fac858' },
      },
      {
        name: '健康指数',
        type: 'line',
        yAxisIndex: 1,
        data: healthSeries,
        smooth: true,
        connectNulls: false,
        itemStyle: { color: isAnyWarning ? '#ff4d4f' : '#ee6666' },
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
              { offset: 0, color: isAnyWarning ? 'rgba(255,77,79,0.35)' : 'rgba(238,102,102,0.25)' },
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
  flex-wrap: wrap;
  gap: 12px;
}

.card-header h2 {
  margin: 0;
  font-size: 22px;
  color: #1a1a2e;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
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

.selector select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.patrol-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
}

.switch {
  position: relative;
  display: inline-block;
  width: 40px;
  height: 22px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: 0.3s;
  border-radius: 22px;
}

.slider::before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #1890ff;
}

input:checked + .slider::before {
  transform: translateX(18px);
}

.patrol-label {
  font-size: 13px;
  color: #555;
  white-space: nowrap;
}

.patrol-countdown {
  font-size: 12px;
  color: #1890ff;
  font-weight: 600;
  background: #e6f7ff;
  padding: 2px 8px;
  border-radius: 10px;
  min-width: 30px;
  text-align: center;
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

.missing-hint {
  background: #fffbe6;
  border: 1px solid #ffe58f;
  color: #d48806;
  padding: 8px 12px;
  border-radius: 6px;
  margin-bottom: 12px;
  font-size: 13px;
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

<style>
.alert-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
  animation: alert-fade-in 0.3s ease;
}

.alert-box {
  background: #fff;
  border: 3px solid #ff4d4f;
  border-radius: 16px;
  padding: 36px 44px;
  max-width: 460px;
  text-align: center;
  box-shadow: 0 0 60px rgba(255, 77, 79, 0.45);
  animation: alert-pulse 1.2s ease-in-out infinite alternate;
}

.alert-icon {
  font-size: 52px;
  margin-bottom: 12px;
  animation: alert-shake 0.5s ease-in-out infinite;
}

.alert-title {
  font-size: 22px;
  font-weight: 700;
  color: #cf1322;
  margin-bottom: 14px;
}

.alert-body {
  font-size: 15px;
  color: #333;
  line-height: 1.8;
  margin-bottom: 24px;
}

.alert-score {
  color: #cf1322;
  font-size: 17px;
}

.alert-btn {
  background: #ff4d4f;
  color: #fff;
  border: none;
  padding: 10px 40px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s, transform 0.1s;
}

.alert-btn:hover {
  background: #d9363e;
}

.alert-btn:active {
  transform: scale(0.97);
}

@keyframes alert-fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes alert-pulse {
  from { box-shadow: 0 0 40px rgba(255, 77, 79, 0.35); }
  to { box-shadow: 0 0 70px rgba(255, 77, 79, 0.6); }
}

@keyframes alert-shake {
  0%, 100% { transform: rotate(0deg); }
  20% { transform: rotate(-8deg); }
  40% { transform: rotate(8deg); }
  60% { transform: rotate(-5deg); }
  80% { transform: rotate(5deg); }
}
</style>
