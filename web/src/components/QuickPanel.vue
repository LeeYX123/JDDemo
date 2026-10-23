<script setup>
import { computed } from 'vue'

import Icon from './Icon.vue'
import { useShopStore } from '../stores'

const props = defineProps({
  notices: { type: Array, default: () => [] },
})

const shop = useShopStore()
const user = computed(() => shop.user)
const list = computed(() => (props.notices.length ? props.notices.slice(0, 5) : []))

const ICONS = [
  { icon: 'phone', label: '话费充值' },
  { icon: 'truck', label: '机票酒店' },
  { icon: 'play', label: '电影票' },
  { icon: 'location', label: '旅行' },
  { icon: 'bag', label: '拍拍二手' },
  { icon: 'crown', label: 'PLUS' },
  { icon: 'wallet', label: '京东金融' },
  { icon: 'comment', label: '客户服务' },
  { icon: 'coupon', label: '领券中心' },
]
</script>

<template>
  <aside class="quick-panel">
    <div class="user-card">
      <span class="avatar">{{ user ? (user.nickname || user.username).slice(0, 1) : '京' }}</span>
      <div>
        <div class="u-name">
          <template v-if="user">Hi，{{ user.nickname || user.username }}</template>
          <template v-else>Hi，欢迎来到京东</template>
        </div>
        <div class="u-sub">
          <template v-if="user"><RouterLink to="/user">个人中心</RouterLink> · 京东会员</template>
          <template v-else><RouterLink to="/login">登录</RouterLink> 后享更多权益</template>
        </div>
      </div>
    </div>

    <div class="user-actions">
      <RouterLink to="/coupons" class="solid">新人福利</RouterLink>
      <RouterLink to="/coupons">PLUS会员</RouterLink>
    </div>

    <div class="news">
      <div class="news-head">
        <h3>京东快报</h3>
        <RouterLink to="/seckill">更多 ›</RouterLink>
      </div>
      <RouterLink v-for="notice in list" :key="notice.id" to="/seckill" class="news-item">
        <em>{{ notice.category || '热' }}</em
        ><span class="news-text">{{ notice.title }}</span>
      </RouterLink>
    </div>

    <div class="quick-icons">
      <a v-for="item in ICONS" :key="item.label" @click="$router.push('/search')">
        <span class="qi"><Icon :name="item.icon" :size="16" /></span>
        {{ item.label }}
      </a>
    </div>
  </aside>
</template>
