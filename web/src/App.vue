<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { RouterView } from 'vue-router'

import { useShopStore } from './stores'

const shop = useShopStore()
const showTop = ref(false)

function onScroll() {
  showTop.value = window.scrollY > 700
}
function toTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(() => window.addEventListener('scroll', onScroll, { passive: true }))
onUnmounted(() => window.removeEventListener('scroll', onScroll))
</script>

<template>
  <RouterView />
  <transition name="toast">
    <div v-if="shop.toast" class="toast"><span class="toast-dot">✓</span>{{ shop.toast }}</div>
  </transition>
  <transition name="fade">
    <button v-if="showTop" class="back-top" title="回到顶部" @click="toTop">↑</button>
  </transition>
</template>
