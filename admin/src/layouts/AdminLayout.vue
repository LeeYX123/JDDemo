<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'

import AppIcon from '../components/AppIcon.vue'
import { MENUS, ROLE_LABEL } from '../menus'
import { api } from '../api'
import { useAuthStore } from '../store/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const area = computed(() => (route.path.startsWith('/console') ? 'console' : 'merchant'))
const menus = computed(() => MENUS[area.value])
const currentTitle = computed(() => route.meta.title || '')
const badges = ref({})

const canSwitch = computed(() => auth.isConsole)
const isActive = (item) => route.path === item.path

async function loadBadges() {
  try {
    if (area.value === 'merchant') {
      const data = await api.get('/merchant/dashboard/')
      badges.value = data.stats || {}
    } else {
      const data = await api.get('/console/dashboard/')
      badges.value = data.stats || {}
    }
  } catch {
    badges.value = {}
  }
}

function badgeCount(key) {
  const value = Number(badges.value[key] || 0)
  return value > 0 ? value : 0
}

function switchArea(target) {
  router.push(`/${target}/dashboard`)
}

async function logout() {
  try {
    await ElMessageBox.confirm('确定退出当前账号吗？', '退出登录', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  auth.logout()
  router.push('/login')
}

watch(area, loadBadges, { immediate: true })
watch(() => route.path, loadBadges)
</script>

<template>
  <div class="admin-shell" :class="{ 'console-shell': area === 'console' }">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark">京</span>
        <div class="brand-text">
          <b>JD DEMO</b>
          <span>{{ area === 'console' ? 'PLATFORM CONSOLE' : 'MERCHANT CENTER' }}</span>
        </div>
      </div>

      <div v-if="canSwitch" class="role-switch">
        <button :class="{ on: area === 'merchant' }" @click="switchArea('merchant')">商家端</button>
        <button :class="{ on: area === 'console' }" @click="switchArea('console')">平台端</button>
      </div>

      <nav class="menu">
        <p class="menu-label">{{ ROLE_LABEL[area] }}</p>
        <RouterLink
          v-for="item in menus"
          :key="item.key"
          :to="item.path"
          class="menu-item"
          :class="{ on: isActive(item) }"
        >
          <AppIcon :name="item.icon" :size="17" />
          <span>{{ item.label }}</span>
          <i v-if="item.badge && badgeCount(item.badge)" class="menu-badge">
            {{ badgeCount(item.badge) }}
          </i>
        </RouterLink>
      </nav>

      <div class="sidebar-foot">
        <a href="http://localhost:5173" target="_blank" rel="noreferrer">↗ 访问买家端商城</a>
        <span>演示环境 · 数据每日可重置</span>
      </div>
    </aside>

    <div class="main-area">
      <header class="topbar">
        <div class="crumb">
          <span>{{ ROLE_LABEL[area] }}</span>
          <span class="sep">/</span>
          <b>{{ currentTitle }}</b>
        </div>

        <div class="topbar-right">
          <a class="topbar-link" href="http://localhost:5173" target="_blank" rel="noreferrer">前台首页</a>
          <div class="topbar-user" @click="logout">
            <span class="avatar">{{ auth.displayName.slice(0, 1) }}</span>
            <span class="who">
              {{ auth.displayName }}
              <small>{{ area === 'console' ? '平台运营' : '店铺管理员' }} · 退出</small>
            </span>
          </div>
        </div>
      </header>

      <main class="content">
        <RouterView />
      </main>
    </div>
  </div>
</template>
