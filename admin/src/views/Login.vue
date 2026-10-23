<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { useAuthStore } from '../store/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const form = reactive({ username: '13900139000', password: '123456' })
const loading = ref(false)
const error = ref('')

const DEMOS = [
  { label: '商家账号', phone: '13900139000', desc: '星野数码旗舰店' },
  { label: '平台账号', phone: '13700137000', desc: '平台运营管理员' },
]

function fill(demo) {
  form.username = demo.phone
  form.password = '123456'
  error.value = ''
}

async function submit() {
  error.value = ''
  if (!/^\d{11}$/.test(form.username)) {
    error.value = '请输入 11 位手机号'
    return
  }
  if (form.password.length < 6) {
    error.value = '密码至少 6 位'
    return
  }
  loading.value = true
  try {
    const user = await auth.login(form.username, form.password)
    ElMessage.success(`欢迎回来，${user.nickname || user.username}`)
    const redirect = route.query.redirect
    const target =
      typeof redirect === 'string' && redirect.startsWith('/')
        ? redirect
        : user.role === 'console'
          ? '/console/dashboard'
          : '/merchant/dashboard'
    router.replace(target)
  } catch (err) {
    error.value = err.message || '登录失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <section class="login-hero">
      <div class="mark"><i>京</i>JD DEMO 运营后台</div>
      <h1>一个后台<br />管好整座商城</h1>
      <p>
        商家端负责商品、订单、售后与店铺经营；平台端负责类目、审核、内容运营与全站数据。
        两端共用一套接口，按角色渲染菜单与路由。
      </p>
      <ul>
        <li>商家数据严格隔离，平台可跨店查询</li>
        <li>轮播 / 楼层 / 快报改完即对前台生效</li>
        <li>商品审核通过才会上架，驳回需填写原因</li>
        <li>售后同意自动回滚库存与订单状态</li>
      </ul>
    </section>

    <section class="login-panel">
      <div class="login-card">
        <h2>登录运营后台</h2>
        <p>请使用商家或平台账号登录，买家账号请前往买家端</p>

        <form @submit.prevent="submit">
          <el-input v-model="form.username" size="large" maxlength="11" placeholder="手机号" />
          <el-input
            v-model="form.password"
            size="large"
            type="password"
            show-password
            placeholder="密码"
            @keyup.enter="submit"
          />
          <p v-if="error" class="login-error">{{ error }}</p>
          <el-button type="primary" size="large" native-type="submit" :loading="loading">
            {{ loading ? '登录中…' : '登 录' }}
          </el-button>
        </form>

        <div class="demo-box">
          <p>演示账号（密码均为 123456，点击一键填充）</p>
          <div class="demo-btns">
            <button v-for="demo in DEMOS" :key="demo.phone" type="button" @click="fill(demo)">
              <b>{{ demo.label }}</b>
              <span>{{ demo.phone }} · {{ demo.desc }}</span>
            </button>
          </div>
        </div>

        <p class="login-foot">
          买家端入口 <a href="http://localhost:5173" target="_blank" rel="noreferrer">localhost:5173</a><br />
          本项目为京东版式还原演示，与京东官方无关
        </p>
      </div>
    </section>
  </div>
</template>
