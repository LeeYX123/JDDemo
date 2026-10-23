<script setup>
import { computed } from 'vue'

import ProductImage from './ProductImage.vue'

const props = defineProps({
  product: { type: Object, required: true },
  size: { type: String, default: 'md' },
  showTags: { type: Boolean, default: true },
})

const priceParts = computed(() => {
  const value = Number(props.product.price || 0).toFixed(2)
  const [int, dec] = value.split('.')
  return { int, dec }
})
const salesText = computed(() => {
  const n = Number(props.product.sales || 0)
  if (n >= 10000) return `已售 ${(n / 10000).toFixed(1)}万+`
  return `已售 ${n}+`
})
const tags = computed(() => (props.product.tag_list || []).slice(0, 2))
</script>

<template>
  <RouterLink :to="`/item/${product.id}`" class="product-card" :class="`card-${size}`">
    <div class="card-img-wrap">
      <ProductImage :seed="product.image_seed" :size="size === 'lg' ? 'lg' : 'md'" :title="product.title" />
      <span v-if="tags.length" class="card-tags">
        <i v-for="tag in tags" :key="tag" class="tag tag-plain">{{ tag }}</i>
      </span>
    </div>
    <div class="card-price">
      <span class="symbol">¥</span><span class="int">{{ priceParts.int }}</span
      ><span class="dec">.{{ priceParts.dec }}</span>
      <span v-if="Number(product.market_price) > Number(product.price)" class="price-origin">
        ¥{{ Number(product.market_price).toFixed(0) }}
      </span>
    </div>
    <h3 class="card-title" :title="product.title">{{ product.title }}</h3>
    <div class="card-meta">
      <span>{{ salesText }}</span>
      <span>{{ product.review_count || 0 }} 条评价</span>
    </div>
  </RouterLink>
</template>
