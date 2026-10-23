<script setup>
import { useRouter } from 'vue-router'

import ShopLayout from '../components/ShopLayout.vue'

const router = useRouter()
</script>

<template>
  <ShopLayout>
    <main class="wrap notfound">
      <div class="nf-code">404</div>
      <h1>抱歉，你访问的页面不存在</h1>
      <p>可能已被删除，或者链接地址有误</p>
      <div class="nf-actions">
        <button class="btn btn-primary" @click="router.push('/')">返回首页</button>
        <button class="btn btn-plain" @click="router.back()">返回上一页</button>
      </div>
    </main>
  </ShopLayout>
</template>
