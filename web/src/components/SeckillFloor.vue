<script setup>
import { computed } from 'vue'

import Icon from './Icon.vue'
import ProductImage from './ProductImage.vue'
import { useCountdown } from '../utils/countdown'

const props = defineProps({
  seckill: { type: Object, default: null },
})

const items = computed(() => (props.seckill?.items || []).slice(0, 6))
const { parts } = useCountdown(props.seckill?.end_at || new Date())
const label = computed(() => props.seckill?.label || '10:00 场')
</script>

<template>
  <section v-if="items.length" class="seckill-floor">
    <div class="seckill-head">
      <h2>京东秒杀</h2>
      <span class="label">{{ label }}</span>
      <span class="countdown">
        <b>{{ parts.hours }}</b
        >:<b>{{ parts.minutes }}</b
        >:<b>{{ parts.seconds }}</b>
        后结束
      </span>
      <RouterLink to="/seckill" class="more">更多秒杀<Icon name="chevron-right" :size="12" /></RouterLink>
    </div>
    <div class="seckill-grid">
      <RouterLink v-for="item in items" :key="item.id" :to="`/item/${item.spu_id}`" class="flash-card">
        <div class="fc-img"><ProductImage :seed="item.image_seed" size="md" :title="item.title" /></div>
        <div class="fc-price">
          ¥{{ Number(item.seckill_price).toFixed(2) }}
          <span class="origin">¥{{ Number(item.market_price).toFixed(0) }}</span>
        </div>
        <div class="fc-title">{{ item.title }}</div>
        <div class="fc-progress">
          <i :style="{ width: Math.min(100, (item.sold / item.limit_stock) * 100) + '%' }" />
          <span>已抢 {{ item.sold }} 件</span>
        </div>
      </RouterLink>
    </div>
  </section>
</template>
