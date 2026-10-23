<script setup>
import { useRouter } from 'vue-router'

import Icon from './Icon.vue'
import { useShopStore } from '../stores'

const shop = useShopStore()
const router = useRouter()

function logout() {
  shop.logout()
  router.push('/')
}
</script>

<template>
  <div class="topbar">
    <div class="wrap topbar-in">
      <span class="hello">
        <template v-if="shop.user">
          您好，<b class="red">{{ shop.user.nickname || shop.user.username }}</b>
          <a class="red" @click="logout">退出</a>
        </template>
        <template v-else>
          您好，请登录
          <RouterLink to="/login" class="red">免费注册</RouterLink>
        </template>
      </span>
      <div class="top-links">
        <RouterLink to="/user"><Icon name="user" :size="12" />我的京东</RouterLink>
        <RouterLink to="/orders">我的订单</RouterLink>
        <RouterLink to="/coupons">京东会员</RouterLink>
        <span>企业采购</span>
        <span>客户服务<Icon name="chevron-down" :size="10" /></span>
        <span>网站导航<Icon name="chevron-down" :size="10" /></span>
        <span>手机京东</span>
      </div>
    </div>
  </div>
</template>
