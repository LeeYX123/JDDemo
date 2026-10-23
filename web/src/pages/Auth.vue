<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api } from '../api'
import Icon from '../components/Icon.vue'
import Logo from '../components/Logo.vue'
import { useShopStore } from '../stores'

const route = useRoute()
const router = useRouter()
const shop = useShopStore()

const isRegister = computed(() => route.path === '/register')
const loading = ref(false)
const error = ref('')
const form = reactive({
  username: '13800138000',
  password: '123456',
  captcha: '',
  nickname: '',
})

const DEMOS = [
  { label: '买家', phone: '13800138000', role: '买买买' },
  { label: '商家', phone: '13900139000', role: '开店卖货' },
  { label: '平台', phone: '13700137000', role: '平台运营' },
]

const BENEFITS = ['正品保障，全国联保', '京东物流，次日送达', '7 天无理由退货', 'PLUS 会员专属折扣']

function fill(demo) {
  form.username = demo.phone
  form.password = '123456'
  form.captcha = '8888'
  error.value = ''
}

function getCaptcha() {
  form.captcha = '8888'
  shop.showToast('演示验证码为 8888')
}

function redirectTarget() {
  const next = route.query.next
  return typeof next === 'string' && next.startsWith('/') ? next : '/'
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
    if (isRegister.value) {
      const data = await api.post('/auth/register/', {
        username: form.username,
        password: form.password,
        captcha: form.captcha,
        nickname: form.nickname,
      })
      localStorage.setItem('jd_access', data.access)
      localStorage.setItem('jd_refresh', data.refresh)
      shop.setUser(data.user)
      await shop.loadCart()
      shop.showToast('注册成功，欢迎加入京东')
      router.push(redirectTarget())
    } else {
      const user = await shop.login(form.username, form.password)
      if (user.role === 'merchant' || user.role === 'console') {
        shop.showToast('登录成功，请前往后台 http://localhost:5174')
      } else {
        shop.showToast('登录成功')
      }
      router.push(redirectTarget())
    }
  } catch (err) {
    error.value = err.message || '登录失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

watch(
  () => route.path,
  () => {
    error.value = ''
  }
)
</script>

<template>
  <div class="auth-page">
    <div class="auth-topbar">
      <div class="wrap auth-topbar-in">
        <RouterLink to="/"><Logo /></RouterLink>
        <span class="auth-welcome">欢迎登录京东</span>
        <RouterLink to="/" class="auth-back">返回首页 ›</RouterLink>
      </div>
    </div>

    <div class="wrap auth-main">
      <aside class="auth-banner">
        <h2>品质生活<br />从京东开始</h2>
        <p>超 10 万品牌正品好物，京东物流极速送达</p>
        <ul>
          <li v-for="item in BENEFITS" :key="item"><Icon name="check" :size="13" />{{ item }}</li>
        </ul>
        <div class="auth-art"><span>JD</span></div>
      </aside>

      <section class="auth-card">
        <div class="auth-tabs">
          <RouterLink to="/login" :class="{ on: !isRegister }">登录</RouterLink>
          <RouterLink to="/register" :class="{ on: isRegister }">注册</RouterLink>
        </div>

        <form class="auth-form" @submit.prevent="submit">
          <div class="auth-field">
            <span class="af-icon"><Icon name="user" :size="16" /></span>
            <input v-model="form.username" placeholder="手机号" maxlength="11" autocomplete="username" />
          </div>
          <div class="auth-field">
            <span class="af-icon"><Icon name="shield" :size="16" /></span>
            <input
              v-model="form.password"
              type="password"
              placeholder="密码（至少 6 位）"
              autocomplete="current-password"
            />
          </div>
          <div v-if="isRegister" class="auth-field">
            <span class="af-icon"><Icon name="phone" :size="16" /></span>
            <input v-model="form.captcha" placeholder="短信验证码（演示固定 8888）" maxlength="4" />
            <button type="button" class="captcha-btn" @click="getCaptcha">获取验证码</button>
          </div>
          <div v-if="isRegister" class="auth-field">
            <span class="af-icon"><Icon name="edit" :size="16" /></span>
            <input v-model="form.nickname" placeholder="昵称（选填）" maxlength="20" />
          </div>

          <p v-if="error" class="auth-error">{{ error }}</p>

          <button class="auth-submit" type="submit" :disabled="loading">
            {{ loading ? '处理中…' : isRegister ? '立即注册' : '登 录' }}
          </button>

          <div class="auth-links">
            <span>忘记密码？</span>
            <span>|</span>
            <RouterLink :to="isRegister ? '/login' : '/register'">
              {{ isRegister ? '已有账号，去登录' : '免费注册' }}
            </RouterLink>
          </div>
        </form>

        <div class="demo-accounts">
          <p>演示账号，点击一键填充（密码均为 123456）</p>
          <div class="demo-btns">
            <button v-for="demo in DEMOS" :key="demo.phone" @click="fill(demo)">
              <b>{{ demo.label }}</b
              ><span>{{ demo.phone }}</span
              ><em>{{ demo.role }}</em>
            </button>
          </div>
          <p class="demo-tip">商家 / 平台账号登录后可前往 <b>http://localhost:5174</b> 进入后台</p>
        </div>
      </section>
    </div>

    <div class="auth-footer">© 2004 - 2026 京东JD.com 版权所有 · 本项目为版式还原演示</div>
  </div>
</template>
