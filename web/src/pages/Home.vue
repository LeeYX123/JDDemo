<script setup>
import { onMounted, onUnmounted, ref } from 'vue'

import { api } from '../api'
import CategoryMenu from '../components/CategoryMenu.vue'
import HeroCarousel from '../components/HeroCarousel.vue'
import ProductCard from '../components/ProductCard.vue'
import ProductFloor from '../components/ProductFloor.vue'
import PromoColumn from '../components/PromoColumn.vue'
import QuickPanel from '../components/QuickPanel.vue'
import SeckillFloor from '../components/SeckillFloor.vue'
import ShopLayout from '../components/ShopLayout.vue'

const data = ref(null)
const guess = ref([])
const loading = ref(true)
const loadingMore = ref(false)
const page = ref(2)
const noMore = ref(false)

async function load() {
  loading.value = true
  try {
    data.value = await api.get('/home/')
    guess.value = data.value.guess || []
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  if (loading.value || loadingMore.value || noMore.value) return
  loadingMore.value = true
  try {
    const res = await api.get('/products/', { page: page.value, size: 12, ordering: 'default' })
    const exists = new Set(guess.value.map((item) => item.id))
    const rows = (res.results || []).filter((item) => !exists.has(item.id))
    guess.value = guess.value.concat(rows)
    page.value += 1
    if (!res.results?.length || page.value > 8) noMore.value = true
  } finally {
    loadingMore.value = false
  }
}

function onScroll() {
  const nearBottom = window.innerHeight + window.scrollY >= document.body.offsetHeight - 500
  if (nearBottom) loadMore()
}

onMounted(() => {
  load()
  window.addEventListener('scroll', onScroll, { passive: true })
})
onUnmounted(() => window.removeEventListener('scroll', onScroll))
</script>

<template>
  <ShopLayout>
    <main class="home">
      <div class="wrap">
        <div v-if="loading" class="home-skeleton">
          <div class="sk-hero" />
          <div class="sk-row" />
        </div>

        <template v-else-if="data">
          <section class="hero">
            <CategoryMenu :categories="data.categories" />
            <HeroCarousel :banners="data.banners" />
            <QuickPanel :notices="data.notices" />
            <PromoColumn :seckill="data.seckill" />
          </section>

          <SeckillFloor :seckill="data.seckill" />

          <ProductFloor v-for="floor in data.floors" :key="floor.id" :floor="floor" />

          <section class="guess">
            <div class="guess-head"><h2>猜你喜欢</h2></div>
            <div class="guess-grid">
              <ProductCard v-for="product in guess" :key="product.id" :product="product" />
            </div>
            <div class="guess-more">
              <span v-if="loadingMore">正在加载更多好物…</span>
              <span v-else-if="noMore">已经到底啦，去上面逛逛吧</span>
              <span v-else>滚动到底部自动加载</span>
            </div>
          </section>
        </template>
      </div>
    </main>
  </ShopLayout>
</template>
