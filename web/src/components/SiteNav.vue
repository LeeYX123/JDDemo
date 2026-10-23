<script setup>
import Icon from './Icon.vue'

const LINKS = [
  { label: '手机数码', q: '手机' },
  { label: '家用电器', q: '家电' },
  { label: '电脑办公', q: '笔记本' },
  { label: '家居家装', q: '家居' },
  { label: '服饰鞋包', q: '服饰' },
  { label: '美妆护肤', q: '护肤' },
  { label: '食品生鲜', q: '生鲜' },
  { label: '京东超市', q: '超市' },
]
</script>

<template>
  <nav class="nav">
    <div class="wrap nav-in">
      <RouterLink to="/search" class="all-cats">
        全部商品分类<Icon name="chevron-down" :size="13" />
      </RouterLink>
      <div class="nav-links">
        <RouterLink to="/" class="hot">首页</RouterLink>
        <RouterLink v-for="link in LINKS" :key="link.label" :to="{ path: '/search', query: { q: link.q } }">
          {{ link.label }}
        </RouterLink>
        <RouterLink to="/seckill" class="hot">京东秒杀</RouterLink>
        <RouterLink to="/coupons">领券中心</RouterLink>
      </div>
    </div>
  </nav>
</template>
