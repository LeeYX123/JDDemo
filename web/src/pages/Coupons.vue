<script setup>
import { computed, onMounted, ref } from 'vue'

import { api } from '../api'
import Icon from '../components/Icon.vue'
import ShopLayout from '../components/ShopLayout.vue'
import { useShopStore } from '../stores'

const shop = useShopStore()
const coupons = ref([])
const mine = ref(false)
const loading = ref(true)

const visible = computed(() => (mine.value ? coupons.value.filter((c) => c.claimed_by_me) : coupons.value))

async function load() {
  loading.value = true
  try {
    coupons.value = (await api.get('/coupons/', mine.value ? { mine: 1 } : {})) || []
  } finally {
    loading.value = false
  }
}

function showAll() {
  mine.value = false
  load()
}

function toggleMine() {
  if (!shop.isLogin) {
    shop.showToast('登录后可查看已领取的优惠券')
    return
  }
  mine.value = !mine.value
  load()
}

async function claim(coupon) {
  if (!shop.isLogin) {
    shop.showToast('请先登录后再领取')
    return
  }
  if (coupon.claimed_by_me) return
  await api.post('/coupons/', { coupon_id: coupon.id })
  coupon.claimed_by_me = true
  coupon.claimed += 1
  shop.showToast('优惠券已放入账户')
}

onMounted(load)
</script>

<template>
  <ShopLayout>
    <main class="wrap coupons-page">
      <div class="breadcrumb">
        <RouterLink to="/">首页</RouterLink><span class="sep">›</span><span class="current">领券中心</span>
      </div>

      <section class="coupon-hero">
        <div class="ch-copy">
          <small>JD COUPON CENTER</small>
          <h1>领券中心</h1>
          <p>每天 10 点更新，先领券再下单，最高立减 100 元</p>
          <div class="ch-tags">
            <span>满 99 减 20</span><span>满 499 减 50</span><span>家电专享 100 元</span>
          </div>
        </div>
        <div class="ch-art">🎫</div>
      </section>

      <div class="coupon-toolbar">
        <div class="coupon-tabs">
          <button :class="{ on: !mine }" @click="showAll">全部优惠券</button>
          <button :class="{ on: mine }" @click="toggleMine">我的优惠券</button>
        </div>
        <span class="coupon-tip">优惠券仅限本演示环境使用</span>
      </div>

      <div v-if="loading" class="loading">
        <div class="spinner" />
        正在加载优惠券…
      </div>

      <div v-else-if="visible.length" class="coupon-grid">
        <article
          v-for="coupon in visible"
          :key="coupon.id"
          class="coupon-card"
          :class="{ claimed: coupon.claimed_by_me }"
        >
          <div class="coupon-left">
            <div class="coupon-amount"><span>¥</span>{{ Number(coupon.amount).toFixed(0) }}</div>
            <p>满 {{ Number(coupon.threshold).toFixed(0) }} 元可用</p>
          </div>
          <div class="coupon-right">
            <h3>{{ coupon.name }}</h3>
            <p class="coupon-scope">{{ coupon.scope }}</p>
            <p class="coupon-date">有效期至 {{ coupon.valid_until }}</p>
            <button v-if="coupon.claimed_by_me" class="coupon-btn claimed" disabled>已领取</button>
            <button v-else-if="coupon.claimed >= coupon.total" class="coupon-btn" disabled>已抢光</button>
            <button v-else class="coupon-btn" @click="claim(coupon)">立即领取</button>
          </div>
          <span v-if="coupon.claimed_by_me" class="coupon-stamp">已领取</span>
        </article>
      </div>

      <div v-else class="empty panel">
        <div class="empty-icon"><Icon name="coupon" :size="44" /></div>
        <p>{{ mine ? '还没有领取任何优惠券' : '暂时没有可领取的优惠券' }}</p>
        <button v-if="mine" class="btn btn-primary" @click="showAll">去领券</button>
      </div>
    </main>
  </ShopLayout>
</template>
