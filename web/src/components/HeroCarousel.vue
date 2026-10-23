<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import Icon from './Icon.vue'
import ProductImage from './ProductImage.vue'

const props = defineProps({
  banners: { type: Array, default: () => [] },
})

const router = useRouter()
const index = ref(0)
const paused = ref(false)
let timer = null

const slides = computed(() => (props.banners.length ? props.banners : []))

function next() {
  if (slides.value.length) index.value = (index.value + 1) % slides.value.length
}
function prev() {
  if (slides.value.length) index.value = (index.value - 1 + slides.value.length) % slides.value.length
}
function go(link) {
  if (link && link.startsWith('/')) router.push(link)
  else router.push('/search')
}

onMounted(() => {
  timer = setInterval(() => {
    if (!paused.value) next()
  }, 4000)
})
onUnmounted(() => clearInterval(timer))
watch(slides, () => {
  if (index.value >= slides.value.length) index.value = 0
})
</script>

<template>
  <div class="hero-carousel" @mouseenter="paused = true" @mouseleave="paused = false">
    <div
      v-for="(banner, i) in slides"
      :key="banner.id || i"
      class="hero-slide"
      :class="{ on: i === index }"
      :style="{ background: banner.color || '#ffe6e3' }"
    >
      <div class="hero-copy">
        <span class="kicker">JD SELECT · 京东甄选</span>
        <h1>{{ banner.title }}</h1>
        <p>{{ banner.subtitle || '品质生活，安心之选' }}</p>
        <button class="hero-btn" @click="go(banner.link)">
          立即抢购<Icon name="arrow-right" :size="15" />
        </button>
      </div>
      <div class="hero-art">
        <ProductImage :seed="banner.image_seed || i + 1" size="hero" :title="banner.title" />
      </div>
    </div>

    <button class="hero-arr prev" aria-label="上一张" @click="prev">‹</button>
    <button class="hero-arr next" aria-label="下一张" @click="next">›</button>
    <div class="hero-dots">
      <i v-for="(_, i) in slides" :key="i" :class="{ on: i === index }" @click="index = i" />
    </div>
  </div>
</template>
