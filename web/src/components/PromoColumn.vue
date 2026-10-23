<script setup>
import { computed } from 'vue'

import ProductImage from './ProductImage.vue'
import { useCountdown } from '../utils/countdown'

const props = defineProps({
  seckill: { type: Object, default: null },
})

const items = computed(() => (props.seckill?.items || []).slice(0, 2))
const { parts } = useCountdown(props.seckill?.end_at || new Date())
</script>

<template>
  <aside class="promo-col">
    <div class="promo-seckill">
      <div class="ps-head"><b>京东秒杀</b><span>天天低价</span></div>
      <div class="ps-time">本场 {{ parts.hours }}:{{ parts.minutes }}:{{ parts.seconds }} 后结束</div>
      <RouterLink v-for="item in items" :key="item.id" :to="`/item/${item.spu_id}`" class="ps-item">
        <ProductImage :seed="item.image_seed" size="sm" :title="item.title" />
        <div class="ps-info">
          <div class="ps-price">¥{{ Number(item.seckill_price).toFixed(0) }}</div>
          <div class="ps-name">{{ item.title }}</div>
        </div>
      </RouterLink>
      <RouterLink to="/seckill" class="ps-more">查看全部秒杀 ›</RouterLink>
    </div>

    <RouterLink to="/coupons" class="promo-tile t1">
      <div><b>京东国际</b><span>全球好物 直邮到家</span></div>
      <span class="tile-glyph">🌍</span>
    </RouterLink>
    <RouterLink to="/coupons" class="promo-tile t2">
      <div><b>PLUS 会员</b><span>全年省 2000 元</span></div>
      <span class="tile-glyph">👑</span>
    </RouterLink>
  </aside>
</template>
