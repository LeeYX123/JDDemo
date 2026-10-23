<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import { api } from '../api'
import Icon from '../components/Icon.vue'
import ProductImage from '../components/ProductImage.vue'
import ShopLayout from '../components/ShopLayout.vue'
import { useShopStore } from '../stores'

const shop = useShopStore()

const tab = ref('profile')
const summary = ref(null)
const reviews = ref([])
const addresses = ref([])
const saving = ref(false)
const showAddress = ref(false)
const editingId = ref(null)

const profile = reactive({ nickname: '', phone: '', email: '' })
const addressForm = reactive({
  receiver: '',
  phone: '',
  province: '',
  city: '',
  district: '',
  detail: '',
  tag: '家',
  is_default: false,
})

const MENUS = [
  { key: 'profile', label: '个人资料', icon: 'user' },
  { key: 'address', label: '收货地址', icon: 'location' },
  { key: 'reviews', label: '我的评价', icon: 'comment' },
  { key: 'coupons', label: '我的优惠券', icon: 'coupon', to: '/coupons' },
  { key: 'orders', label: '我的订单', icon: 'bag', to: '/orders' },
]

const stats = computed(() => summary.value || {})
const user = computed(() => shop.user || {})

async function load() {
  summary.value = await api.get('/auth/summary/')
  Object.assign(profile, {
    nickname: user.value.nickname || '',
    phone: user.value.phone || user.value.username || '',
    email: user.value.email || '',
  })
}

async function loadAddresses() {
  addresses.value = (await api.get('/addresses/')) || []
}

async function loadReviews() {
  reviews.value = (await api.get('/reviews/mine/')) || []
}

function openAddress(address = null) {
  editingId.value = address?.id || null
  Object.assign(
    addressForm,
    address || {
      receiver: '',
      phone: '',
      province: '',
      city: '',
      district: '',
      detail: '',
      tag: '家',
      is_default: false,
    }
  )
  showAddress.value = true
}

async function saveProfile() {
  saving.value = true
  try {
    const updated = await api.patch('/auth/me/', { ...profile })
    shop.setUser(updated)
    shop.showToast('资料已保存')
    load()
  } finally {
    saving.value = false
  }
}

async function saveAddress() {
  if (!addressForm.receiver || !addressForm.phone || !addressForm.province || !addressForm.detail) {
    shop.showToast('请填写完整的收货信息')
    return
  }
  if (editingId.value) {
    await api.patch(`/addresses/${editingId.value}/`, { ...addressForm })
  } else {
    await api.post('/addresses/', { ...addressForm })
  }
  showAddress.value = false
  shop.showToast('地址已保存')
  await loadAddresses()
  load()
}

async function removeAddress(address) {
  if (!window.confirm(`确定删除「${address.receiver} ${address.full_text}」吗？`)) return
  await api.delete(`/addresses/${address.id}/`)
  shop.showToast('地址已删除')
  loadAddresses()
  load()
}

async function setDefault(address) {
  await api.patch(`/addresses/${address.id}/`, { is_default: true })
  loadAddresses()
}

function switchTab(key) {
  if (key === 'address' && !addresses.value.length) loadAddresses()
  if (key === 'reviews' && !reviews.value.length) loadReviews()
  tab.value = key
}

onMounted(load)
</script>

<template>
  <ShopLayout>
    <main class="wrap user-page">
      <div class="breadcrumb">
        <RouterLink to="/">首页</RouterLink><span class="sep">›</span><span class="current">个人中心</span>
      </div>

      <div class="user-layout">
        <aside class="user-side panel">
          <div class="u-profile">
            <span class="avatar big">{{ (user.nickname || user.username || '京').slice(0, 1) }}</span>
            <b>{{ user.nickname || user.username || '京东用户' }}</b>
            <small>京东会员 · 铜牌</small>
          </div>
          <nav class="u-menu">
            <button
              v-for="menu in MENUS"
              :key="menu.key"
              :class="{ on: tab === menu.key }"
              @click="menu.to ? $router.push(menu.to) : switchTab(menu.key)"
            >
              <Icon :name="menu.icon" :size="14" />{{ menu.label }}
            </button>
          </nav>
          <div class="u-stats">
            <RouterLink to="/orders" class="u-stat">
              <b>{{ stats.pending_pay || 0 }}</b
              ><span>待付款</span>
            </RouterLink>
            <RouterLink to="/orders" class="u-stat">
              <b>{{ stats.pending_receive || 0 }}</b
              ><span>待收货</span>
            </RouterLink>
            <RouterLink to="/orders" class="u-stat">
              <b>{{ stats.after_sale || 0 }}</b
              ><span>售后中</span>
            </RouterLink>
          </div>
        </aside>

        <section class="user-content panel">
          <div v-if="tab === 'profile'">
            <div class="uc-head">
              <h2>个人资料</h2>
              <span>完善资料，享受更贴心的服务</span>
            </div>
            <div class="profile-form">
              <div class="form-item">
                <label class="form-label">昵称</label>
                <input v-model="profile.nickname" class="form-input" placeholder="给自己起个昵称" />
              </div>
              <div class="form-item">
                <label class="form-label">手机号</label>
                <input v-model="profile.phone" class="form-input" placeholder="11 位手机号" />
              </div>
              <div class="form-item">
                <label class="form-label">邮箱</label>
                <input v-model="profile.email" class="form-input" placeholder="用于接收订单通知" />
              </div>
              <div class="form-item">
                <label class="form-label">账号角色</label>
                <input :value="user.role_label || '买家'" class="form-input" disabled />
              </div>
              <button class="btn btn-primary" :disabled="saving" @click="saveProfile">
                {{ saving ? '保存中…' : '保存修改' }}
              </button>
            </div>
          </div>

          <div v-else-if="tab === 'address'">
            <div class="uc-head">
              <h2>收货地址</h2>
              <button class="btn btn-primary btn-sm" @click="openAddress()">新增地址</button>
            </div>
            <div class="address-manage">
              <article v-for="address in addresses" :key="address.id" class="address-item">
                <div class="am-top">
                  <b>{{ address.receiver }}</b>
                  <span>{{ address.phone }}</span>
                  <i v-if="address.is_default" class="tag">默认</i>
                  <i v-else class="tag tag-gray">{{ address.tag || '地址' }}</i>
                </div>
                <p>{{ address.full_text }}</p>
                <div class="am-actions">
                  <button @click="openAddress(address)">编辑</button>
                  <button @click="removeAddress(address)">删除</button>
                  <button v-if="!address.is_default" @click="setDefault(address)">设为默认</button>
                </div>
              </article>
              <div v-if="!addresses.length" class="empty">
                <p>还没有收货地址</p>
                <button class="btn btn-primary" @click="openAddress()">新增地址</button>
              </div>
            </div>
          </div>

          <div v-else-if="tab === 'reviews'">
            <div class="uc-head">
              <h2>我的评价</h2>
              <span>共 {{ reviews.length }} 条</span>
            </div>
            <div v-if="reviews.length" class="my-reviews">
              <article v-for="review in reviews" :key="review.id" class="my-review">
                <RouterLink :to="`/item/${review.spu_id}`">
                  <ProductImage :seed="review.image_seed" size="sm" :title="review.title" />
                </RouterLink>
                <div class="mr-info">
                  <RouterLink :to="`/item/${review.spu_id}`" class="mr-title">{{ review.title }}</RouterLink>
                  <div class="stars">
                    {{ '★'.repeat(review.rating) }}<i>{{ '★'.repeat(5 - review.rating) }}</i>
                  </div>
                  <p>{{ review.content }}</p>
                  <p v-if="review.reply" class="review-reply">商家回复：{{ review.reply }}</p>
                </div>
                <span class="mr-date">{{ review.created_at }}</span>
              </article>
            </div>
            <div v-else class="empty">
              <p>还没有评价，去订单里晒单吧</p>
              <RouterLink to="/orders" class="btn btn-primary">查看订单</RouterLink>
            </div>
          </div>
        </section>
      </div>

      <div v-if="showAddress" class="modal-mask" @click.self="showAddress = false">
        <div class="modal-card">
          <div class="modal-head">
            <h3>{{ editingId ? '编辑收货地址' : '新增收货地址' }}</h3>
            <button @click="showAddress = false"><Icon name="close" :size="16" /></button>
          </div>
          <div class="modal-body">
            <div class="form-row">
              <div class="form-item">
                <label class="form-label">收货人</label
                ><input v-model="addressForm.receiver" class="form-input" />
              </div>
              <div class="form-item">
                <label class="form-label">手机号</label
                ><input v-model="addressForm.phone" class="form-input" maxlength="11" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-item">
                <label class="form-label">省份</label
                ><input v-model="addressForm.province" class="form-input" placeholder="北京市" />
              </div>
              <div class="form-item">
                <label class="form-label">城市</label
                ><input v-model="addressForm.city" class="form-input" placeholder="北京市" />
              </div>
              <div class="form-item">
                <label class="form-label">区县</label
                ><input v-model="addressForm.district" class="form-input" placeholder="朝阳区" />
              </div>
            </div>
            <div class="form-item">
              <label class="form-label">详细地址</label
              ><input v-model="addressForm.detail" class="form-input" />
            </div>
            <div class="form-row">
              <div class="form-item">
                <label class="form-label">标签</label>
                <select v-model="addressForm.tag" class="form-input">
                  <option>家</option>
                  <option>公司</option>
                  <option>学校</option>
                </select>
              </div>
              <label class="checkbox address-default"
                ><input v-model="addressForm.is_default" type="checkbox" />设为默认地址</label
              >
            </div>
          </div>
          <div class="modal-foot">
            <button class="btn btn-plain" @click="showAddress = false">取消</button>
            <button class="btn btn-primary" @click="saveAddress">保存</button>
          </div>
        </div>
      </div>
    </main>
  </ShopLayout>
</template>
