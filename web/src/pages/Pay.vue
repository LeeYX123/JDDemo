<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { api } from '../api'
import Icon from '../components/Icon.vue'
import ShopLayout from '../components/ShopLayout.vue'
import { useShopStore } from '../stores'
import { useCountdown } from '../utils/countdown'

const route = useRoute()
const shop = useShopStore()

const batch = ref(null)
const loading = ref(true)
const paying = ref(false)
const method = ref('wechat')
const paid = ref(false)
const failed = ref(false)
const deadline = ref(new Date(Date.now() + 30 * 60 * 1000))
const { parts } = useCountdown(deadline)

const METHODS = [
  { key: 'wechat', label: '微信支付', desc: '亿万用户的选择，安全快捷', icon: '💚' },
  { key: 'alipay', label: '支付宝', desc: '支持花呗分期', icon: '💙' },
  { key: 'baitiao', label: '京东白条', desc: '先消费后还款', icon: '🤍' },
  { key: 'card', label: '银行卡', desc: '支持储蓄卡 / 信用卡', icon: '💳' },
]

const orders = computed(() => batch.value?.orders || [])
const firstOrder = computed(() => orders.value[0])
const total = computed(() => Number(batch.value?.total || 0))

async function load() {
  loading.value = true
  try {
    batch.value = await api.get(`/orders/batch/${route.params.orderNo}/`)
    paid.value = !batch.value.payable
    if (firstOrder.value?.created_at) {
      deadline.value = new Date(new Date(firstOrder.value.created_at).getTime() + 30 * 60 * 1000)
    }
  } catch {
    failed.value = true
  } finally {
    loading.value = false
  }
}

async function pay() {
  paying.value = true
  try {
    await api.post('/payment/mock/', { batch_no: route.params.orderNo, method: method.value })
    paid.value = true
    shop.loadCart()
  } finally {
    paying.value = false
  }
}

onMounted(load)
</script>

<template>
  <ShopLayout>
    <main class="wrap pay-page">
      <div class="checkout-steps">
        <div class="ck-step done"><i>1</i>填写核对订单信息</div>
        <div class="ck-line done" />
        <div class="ck-step done"><i>2</i>成功提交订单</div>
        <div class="ck-line" :class="{ done: paid }" />
        <div class="ck-step" :class="{ active: !paid, done: paid }">
          <i>3</i>{{ paid ? '支付完成' : '收银台付款' }}
        </div>
      </div>

      <div v-if="loading" class="loading">
        <div class="spinner" />
        正在打开收银台…
      </div>

      <section v-else-if="failed" class="panel pay-fail">
        <div class="empty">
          <div class="empty-icon">!</div>
          <p>订单不存在或已失效</p>
          <RouterLink to="/orders" class="btn btn-primary">查看我的订单</RouterLink>
        </div>
      </section>

      <template v-else-if="paid">
        <section class="panel pay-result">
          <div class="result-icon">✓</div>
          <h1>支付成功</h1>
          <p class="result-amount">
            实付款：<span class="price price-lg"
              ><span class="symbol">¥</span><span class="price-int">{{ total.toFixed(2) }}</span></span
            >
          </p>
          <p class="result-tip">商家将尽快为你发货，可在「我的订单」中查看物流进度</p>
          <div class="result-actions">
            <RouterLink v-if="firstOrder" :to="`/orders/${firstOrder.order_no}`" class="btn btn-primary">
              查看订单
            </RouterLink>
            <RouterLink to="/" class="btn btn-plain">继续购物</RouterLink>
          </div>
        </section>
      </template>

      <template v-else>
        <section class="panel cashier">
          <div class="cashier-head">
            <div>
              <h1>收银台</h1>
              <p>订单提交成功，请尽快完成支付</p>
            </div>
            <div class="pay-countdown">
              支付剩余时间
              <b>{{ parts.minutes }}:{{ parts.seconds }}</b>
            </div>
          </div>

          <div class="cashier-body">
            <div class="order-brief">
              <div class="brief-head">
                <span>订单号：{{ orders.map((o) => o.order_no).join(' / ') }}</span>
                <span>{{ orders.length }} 个包裹</span>
              </div>
              <div v-for="order in orders" :key="order.id" class="brief-order">
                <div v-for="item in order.items" :key="item.id" class="brief-item">
                  <span class="brief-title">{{ item.title_snapshot }}</span>
                  <span class="brief-qty">× {{ item.quantity }}</span>
                  <span class="brief-price">¥{{ Number(item.price_snapshot).toFixed(2) }}</span>
                </div>
                <div class="brief-freight">运费 ¥{{ Number(order.freight).toFixed(2) }}</div>
              </div>
              <div class="brief-total">
                应付金额
                <span class="price price-lg"
                  ><span class="symbol">¥</span><span class="price-int">{{ total.toFixed(2) }}</span></span
                >
              </div>
            </div>

            <div class="pay-methods">
              <h3>选择支付方式</h3>
              <label
                v-for="item in METHODS"
                :key="item.key"
                class="pay-method"
                :class="{ on: method === item.key }"
              >
                <input v-model="method" type="radio" :value="item.key" />
                <span class="pm-icon">{{ item.icon }}</span>
                <span class="pm-info"
                  ><b>{{ item.label }}</b
                  ><i>{{ item.desc }}</i></span
                >
                <span class="pm-check"><Icon name="check" :size="12" /></span>
              </label>
              <p class="pay-note">演示环境为模拟支付，点击「立即支付」即视为支付成功，不会产生真实扣款。</p>
              <button class="btn btn-primary btn-lg pay-btn" :disabled="paying" @click="pay">
                {{ paying ? '支付中…' : `立即支付 ¥${total.toFixed(2)}` }}
              </button>
            </div>
          </div>
        </section>
      </template>
    </main>
  </ShopLayout>
</template>
