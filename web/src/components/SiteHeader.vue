<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import Icon from './Icon.vue'
import Logo from './Logo.vue'
import { useShopStore } from '../stores'

const shop = useShopStore()
const router = useRouter()
const keyword = ref('')

const HOT = ['家电五折', '手机新品', '京东超市', 'PLUS会员', '春日上新', '以旧换新']

function search(word) {
  const q = (word ?? keyword.value).trim()
  if (word) keyword.value = word
  router.push({ path: '/search', query: q ? { q } : {} })
}
</script>

<template>
  <div class="header">
    <div class="wrap header-in">
      <RouterLink to="/" aria-label="京东首页"><Logo /></RouterLink>

      <div class="header-search">
        <form class="search-box" @submit.prevent="search()">
          <input v-model="keyword" placeholder="手机 · 家电 · 服饰 · 食品" aria-label="搜索商品" />
          <button class="search-btn" type="submit"><Icon name="search" :size="18" />搜索</button>
        </form>
        <div class="hotwords">
          <span>热搜：</span>
          <a v-for="word in HOT" :key="word" @click="search(word)">{{ word }}</a>
        </div>
      </div>

      <RouterLink id="cart-entry" to="/cart" class="cart-entry">
        <Icon name="cart" :size="17" />
        <span>我的购物车</span>
        <i v-if="shop.cartCount" class="cart-badge">{{ shop.cartCount > 99 ? '99+' : shop.cartCount }}</i>
      </RouterLink>
    </div>
  </div>
</template>
