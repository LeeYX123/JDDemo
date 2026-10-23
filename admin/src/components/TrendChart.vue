<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: { type: Array, default: () => [] },
  labelKey: { type: String, default: 'date' },
  valueKey: { type: String, default: 'gmv' },
  type: { type: String, default: 'bar' },
  color: { type: String, default: '#e1251b' },
  unit: { type: String, default: '' },
  height: { type: Number, default: 240 },
  formatter: { type: Function, default: null },
})

const W = 760
const PAD = { top: 22, right: 14, bottom: 30, left: 52 }

const rows = computed(() =>
  props.data.map((row) => ({
    label: row[props.labelKey] ?? '',
    value: Number(row[props.valueKey] ?? 0),
    raw: row,
  }))
)

const maxValue = computed(() => {
  const max = Math.max(...rows.value.map((r) => r.value), 1)
  const magnitude = 10 ** Math.floor(Math.log10(max))
  return Math.ceil(max / magnitude) * magnitude
})

const innerW = W - PAD.left - PAD.right
const innerH = computed(() => props.height - PAD.top - PAD.bottom)

const scaleY = (value) => PAD.top + innerH.value - (value / maxValue.value) * innerH.value

const step = computed(() => (rows.value.length ? innerW / rows.value.length : innerW))

const bars = computed(() =>
  rows.value.map((row, index) => {
    const barW = Math.min(30, step.value * 0.46)
    const x = PAD.left + step.value * index + (step.value - barW) / 2
    const y = scaleY(row.value)
    return { ...row, x, y, w: barW, h: Math.max(2, PAD.top + innerH.value - y) }
  })
)

const linePoints = computed(() =>
  rows.value.map((row, index) => ({
    ...row,
    x: PAD.left + step.value * index + step.value / 2,
    y: scaleY(row.value),
  }))
)

const linePath = computed(() =>
  linePoints.value.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ')
)

const areaPath = computed(() => {
  if (!linePoints.value.length) return ''
  const base = PAD.top + innerH.value
  return `${linePath.value} L${linePoints.value.at(-1).x.toFixed(1)} ${base} L${linePoints.value[0].x.toFixed(1)} ${base} Z`
})

const gridLines = computed(() =>
  [0, 0.25, 0.5, 0.75, 1].map((ratio) => {
    const value = maxValue.value * (1 - ratio)
    return { y: PAD.top + innerH.value * ratio, text: format(value) }
  })
)

function format(value) {
  if (props.formatter) return props.formatter(value)
  if (value >= 10000) return `${(value / 10000).toFixed(value >= 100000 ? 0 : 1)}万`
  return `${Math.round(value)}`
}

const barLabel = (row) => `${row.label} ${format(row.value)}${props.unit}`
</script>

<template>
  <div class="chart-wrap">
    <svg :viewBox="`0 0 ${W} ${height}`" role="img" :aria-label="`${valueKey} 趋势图`">
      <g>
        <line
          v-for="(line, i) in gridLines"
          :key="`g${i}`"
          :x1="PAD.left"
          :x2="W - PAD.right"
          :y1="line.y"
          :y2="line.y"
          stroke="#eef1f7"
          stroke-width="1"
        />
        <text
          v-for="(line, i) in gridLines"
          :key="`t${i}`"
          :x="PAD.left - 10"
          :y="line.y + 4"
          text-anchor="end"
          font-size="11"
          fill="#98a2b3"
        >
          {{ line.text }}
        </text>
      </g>

      <template v-if="type === 'bar'">
        <g v-for="bar in bars" :key="bar.label">
          <rect :x="bar.x" :y="bar.y" :width="bar.w" :height="bar.h" :fill="color" rx="3" opacity="0.9">
            <title>{{ barLabel(bar) }}</title>
          </rect>
          <text :x="bar.x + bar.w / 2" :y="bar.y - 6" text-anchor="middle" font-size="10.5" fill="#7c8698">
            {{ format(bar.value) }}
          </text>
        </g>
      </template>

      <template v-else>
        <defs>
          <linearGradient :id="`grad-${color.replace('#', '')}`" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" :stop-color="color" stop-opacity="0.22" />
            <stop offset="100%" :stop-color="color" stop-opacity="0" />
          </linearGradient>
        </defs>
        <path :d="areaPath" :fill="`url(#grad-${color.replace('#', '')})`" />
        <path :d="linePath" fill="none" :stroke="color" stroke-width="2.4" stroke-linejoin="round" />
        <g v-for="point in linePoints" :key="point.label">
          <circle :cx="point.x" :cy="point.y" r="4" fill="#fff" :stroke="color" stroke-width="2.4">
            <title>{{ barLabel(point) }}</title>
          </circle>
        </g>
      </template>

      <g>
        <text
          v-for="(row, i) in rows"
          :key="`x${i}`"
          :x="PAD.left + step * i + step / 2"
          :y="height - 10"
          text-anchor="middle"
          font-size="11"
          fill="#98a2b3"
        >
          {{ row.label }}
        </text>
      </g>
    </svg>
  </div>
</template>
