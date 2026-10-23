<script setup>
import { computed, onMounted, ref } from 'vue'

import { api } from '../api'
import Icon from '../components/Icon.vue'
import ProductImage from '../components/ProductImage.vue'
import ShopLayout from '../components/ShopLayout.vue'
import { useCountdown } from '../utils/countdown'

const activities = ref([])
const activeId = ref(null)
const loading = ref(true)

const active = computed(
  () => activities.value.find((item) => item.id === activeId.value) || activities.value[0] || null
)
const items = computed(() => active.value?.items || [])
const { parts } = useCountdown(active.value?.end_at || new Date())

async function load() {
  loading.value = true
  try {
    activities.value = (await api.get('/seckill/')) || []
    if (activities.value.length) activeId.value = activities.value[0].id
  } finally {
    loading.value = false
  }
}

function progress(item) {
  return Math.min(100, (item.sold / item.limit_stock) * 100)
}

onMounted(load)
</script>

<template>
  <ShopLayout>
    <main class="wrap seckill-page">
      <div class="breadcrumb">
        <RouterLink to="/">首页</RouterLink><span class="sep">›</span><span class="current">京东秒杀</span>
      </div>

      <section class="seckill-banner">
        <div>
          <small>JD SECKILL</small>
          <h1>京东秒杀</h1>
          <p>整点开抢 · 限量好物 · 售完即止</p>
        </div>
        <div class="sb-time">
          <span>本场剩余</span>
          <b>{{ parts.hours }}</b
          >:<b>{{ parts.minutes }}</b
          >:<b>{{ parts.seconds }}</b>
        </div>
      </section>

      <div v-if="loading" class="loading">
        <div class="spinner" />
        正在加载秒杀会场…
      </div>

      <template v-else-if="active">
        <div class="seckill-sessions">
          <button
            v-for="activity in activities"
            :key="activity.id"
            :class="{ on: activity.id === active.id }"
            @click="activeId = activity.id"
          >
            <b>{{ activity.label }}</b>
            <span>{{ activity.status === 'running' ? '抢购中' : '即将开始' }}</span>
          </button>
          <span class="session-tip">每小时一场，整点更新</span>
        </div>

        <div class="seckill-grid-lg">
          <article v-for="item in items" :key="item.id" class="seckill-item">
            <RouterLink :to="`/item/${item.spu_id}`" class="si-img">
              <ProductImage :seed="item.image_seed" size="md" :title="item.title" />
            </RouterLink>
            <div class="si-body">
              <RouterLink :to="`/item/${item.spu_id}`" class="si-title">{{ item.title }}</RouterLink>
              <p class="si-spec">{{ item.spec }}</p>
              <div class="si-price">
                <span class="price"
                  ><span class="symbol">¥</span
                  ><span class="price-int">{{ Number(item.seckill_price).toFixed(2) }}</span></span
                >
                <span class="price-origin">¥{{ Number(item.market_price).toFixed(0) }}</span>
              </div>
              <div class="si-progress">
                <i :style="{ width: progress(item) + '%' }" />
                <span>已抢 {{ item.sold }} / {{ item.limit_stock }}</span>
              </div>
              <RouterLink :to="`/item/${item.spu_id}`" class="btn btn-primary btn-sm si-buy">
                立即抢购
              </RouterLink>
            </div>
          </article>
        </div>

        <p class="seckill-rule">
          <Icon name="clock" :size="13" /> 秒杀商品每人限购 1 件，下单后 30 分钟内未支付订单将自动取消
        </p>
      </template>

      <div v-else class="empty panel">
        <div class="empty-icon"><Icon name="clock" :size="44" /></div>
        <p>当前没有进行中的秒杀活动</p>
        <RouterLink to="/" class="btn btn-primary">去逛逛</RouterLink>
      </div>
    </main>
  </ShopLayout>
</template>
