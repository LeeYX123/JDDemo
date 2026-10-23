<script setup>
import SiteFooter from './SiteFooter.vue'
import SiteHeader from './SiteHeader.vue'
import SiteNav from './SiteNav.vue'
import TopBar from './TopBar.vue'
</script>

<template>
  <div class="shop-layout">
    <TopBar />
    <SiteHeader />
    <SiteNav />
    <slot />
    <SiteFooter />
  </div>
</template>
