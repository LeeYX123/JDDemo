<script setup>
import { computed, ref, watch } from 'vue'

import Icon from './Icon.vue'
import ProductCard from './ProductCard.vue'
import { api } from '../api'

const props = defineProps({
  floor: { type: Object, required: true },
})

const tab = ref(0)
const page = ref(0)
const products = ref(props.floor.products || [])
const loading = ref(false)

watch(
  () => props.floor,
  (floor) => {
    products.value = floor.products || []
    tab.value = 0
    page.value = 0
  }
)

const maxPage = computed(() => Math.max(0, Math.ceil(products.value.length / 6) - 1))
const trackStyle = computed(() => ({ transform: `translateX(-${page.value * 600}px)` }))

async function changeTab(index) {
  if (tab.value === index) return
  tab.value = index
  page.value = 0
  loading.value = true
  try {
    const data = await api.get('/products/', { floor: props.floor.id, tab: index, size: 12 })
    products.value = data.results || []
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="floor">
    <div class="floor-head">
      <h2>{{ floor.name }}</h2>
      <span class="floor-sub">{{ floor.subtitle }}</span>
      <div class="tabs">
        <button
          v-for="(name, i) in floor.tabs || ['热门推荐', '新品上架', '价格亲民']"
          :key="name"
          :class="{ on: tab === i }"
          @click="changeTab(i)"
        >
          {{ name }}
        </button>
      </div>
      <div class="arrs">
        <button :disabled="page <= 0" aria-label="上一页" @click="page--">
          <Icon name="chevron-left" :size="12" />
        </button>
        <button :disabled="page >= maxPage" aria-label="下一页" @click="page++">
          <Icon name="chevron-right" :size="12" />
        </button>
      </div>
    </div>
    <div class="floor-body">
      <div class="floor-track" :style="trackStyle" :class="{ loading }">
        <ProductCard v-for="product in products" :key="product.id" :product="product" />
      </div>
    </div>
  </section>
</template>
