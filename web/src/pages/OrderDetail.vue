<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api } from '../api'
import Icon from '../components/Icon.vue'
import ProductImage from '../components/ProductImage.vue'
import ShopLayout from '../components/ShopLayout.vue'
import { useShopStore } from '../stores'

const route = useRoute()
const router = useRouter()
const shop = useShopStore()

const order = ref(null)
const loading = ref(true)

const STEPS = ['提交订单', '付款成功', '商家发货', '确认收货', '交易完成']
const STATUS_INDEX = {
  pending_pay: 0,
  paid: 1,
  shipped: 2,
  completed: 4,
  aftersale: 3,
  cancelled: -1,
  refunded: -1,
}

const stepIndex = computed(() => STATUS_INDEX[order.value?.status] ?? 0)
const isClosed = computed(() => ['cancelled', 'refunded'].includes(order.value?.status))

async function load() {
  loading.value = true
  try {
    order.value = await api.get(`/orders/${route.params.orderNo}/`)
  } finally {
    loading.value = false
  }
}

async function cancel() {
  if (!window.confirm('确定取消该订单吗？')) return
  await api.post(`/orders/${order.value.order_no}/cancel/`)
  shop.showToast('订单已取消')
  load()
}

async function confirmReceive() {
  if (!window.confirm('确认已收到商品吗？')) return
  await api.post(`/orders/${order.value.order_no}/confirm/`)
  shop.showToast('已确认收货')
  load()
}

function pay() {
  router.push(`/pay/${order.value.batch_no || order.value.order_no}`)
}

onMounted(load)
</script>

<template>
  <ShopLayout>
    <main class="wrap order-detail-page">
      <div class="breadcrumb">
        <RouterLink to="/">首页</RouterLink><span class="sep">›</span>
        <RouterLink to="/orders">我的订单</RouterLink><span class="sep">›</span>
        <span class="current">订单详情</span>
      </div>

      <div v-if="loading" class="loading">
        <div class="spinner" />
        正在加载订单详情…
      </div>

      <template v-else-if="order">
        <section class="od-head panel">
          <div class="od-status">
            <h1>{{ order.status_label }}</h1>
            <p v-if="order.status === 'pending_pay'">请尽快完成支付，超时订单将自动取消</p>
            <p v-else-if="order.status === 'paid'">商家正在备货，预计 24 小时内发出</p>
            <p v-else-if="order.status === 'shipped'">商品已发出，请注意查收</p>
            <p v-else-if="order.status === 'completed'">交易已完成，感谢你的支持</p>
            <p v-else-if="order.status === 'cancelled'">订单已取消，库存已回滚</p>
            <p v-else-if="order.status === 'aftersale'">售后处理中，请留意商家回复</p>
            <p v-else>退款已完成</p>
          </div>
          <div class="od-actions">
            <button v-if="order.can_pay" class="btn btn-primary" @click="pay">立即付款</button>
            <button v-if="order.can_cancel" class="btn btn-plain" @click="cancel">取消订单</button>
            <button v-if="order.can_confirm" class="btn btn-primary" @click="confirmReceive">确认收货</button>
            <RouterLink to="/orders" class="btn btn-plain">返回订单列表</RouterLink>
          </div>
        </section>

        <section v-if="!isClosed" class="steps panel">
          <div
            v-for="(step, i) in STEPS"
            :key="step"
            class="step"
            :class="{ done: i < stepIndex, active: i === stepIndex }"
          >
            <span class="dot">{{ i < stepIndex ? '✓' : i + 1 }}</span>
            <div>{{ step }}</div>
            <small v-if="i === 1 && order.paid_at">{{
              String(order.paid_at).slice(0, 16).replace('T', ' ')
            }}</small>
            <small v-if="i === 2 && order.shipped_at">{{
              String(order.shipped_at).slice(0, 16).replace('T', ' ')
            }}</small>
            <small v-if="i === 4 && order.completed_at">{{
              String(order.completed_at).slice(0, 16).replace('T', ' ')
            }}</small>
          </div>
        </section>

        <section class="panel od-block">
          <div class="od-block-head"><h2>收货信息</h2></div>
          <div class="od-address">
            <p>
              <b>{{ order.address_snapshot?.receiver }}</b> {{ order.address_snapshot?.phone }}
            </p>
            <p>{{ order.address_snapshot?.full_text }}</p>
          </div>
          <div v-if="order.tracking_no" class="od-logistics">
            <Icon name="truck" :size="15" />
            <b>{{ order.tracking_company }}</b>
            <span>运单号 {{ order.tracking_no }}</span>
            <em>商品已发出</em>
          </div>
        </section>

        <section class="panel od-block">
          <div class="od-block-head">
            <h2>商品清单</h2>
            <span class="od-shop">{{ (order.shop_names || []).join(' / ') }}</span>
          </div>
          <div v-for="item in order.items" :key="item.id" class="od-item">
            <RouterLink :to="item.spu_id ? `/item/${item.spu_id}` : '#'">
              <ProductImage :seed="item.image_seed" size="sm" :title="item.title_snapshot" />
            </RouterLink>
            <div class="od-item-info">
              <RouterLink :to="item.spu_id ? `/item/${item.spu_id}` : '#'" class="od-item-title">
                {{ item.title_snapshot }}
              </RouterLink>
              <p>{{ Object.values(item.specs_snapshot || {}).join(' / ') }}</p>
              <span v-if="item.aftersale_status" class="tag tag-gray">售后：{{ item.aftersale_status }}</span>
            </div>
            <span class="od-item-price"
              >¥{{ Number(item.price_snapshot).toFixed(2) }} × {{ item.quantity }}</span
            >
            <span class="od-item-sum">¥{{ Number(item.amount).toFixed(2) }}</span>
          </div>

          <div class="od-amount">
            <p>
              <span>商品总额</span><b>¥{{ Number(order.subtotal).toFixed(2) }}</b>
            </p>
            <p>
              <span>运费</span><b>¥{{ Number(order.freight).toFixed(2) }}</b>
            </p>
            <p>
              <span>优惠</span><b>-¥{{ Number(order.discount).toFixed(2) }}</b>
            </p>
            <p class="final">
              <span>实付款</span><b>¥{{ Number(order.total).toFixed(2) }}</b>
            </p>
          </div>
        </section>

        <section class="panel od-block">
          <div class="od-block-head"><h2>订单信息</h2></div>
          <div class="od-meta">
            <p><span>订单编号：</span>{{ order.order_no }}</p>
            <p><span>下单时间：</span>{{ String(order.created_at).replace('T', ' ').slice(0, 19) }}</p>
            <p v-if="order.paid_at">
              <span>付款时间：</span>{{ String(order.paid_at).replace('T', ' ').slice(0, 19) }}
            </p>
            <p><span>支付方式：</span>在线支付（模拟）</p>
            <p v-if="order.remark"><span>订单备注：</span>{{ order.remark }}</p>
          </div>
        </section>

        <section v-if="order.aftersales?.length" class="panel od-block">
          <div class="od-block-head"><h2>售后记录</h2></div>
          <div v-for="sale in order.aftersales" :key="sale.id" class="od-aftersale">
            <div>
              <b>{{ sale.type_label }}</b>
              <span class="tag" :class="{ 'tag-gray': sale.status === 'rejected' }">{{
                sale.status_label
              }}</span>
              <p>原因：{{ sale.reason }}</p>
              <p v-if="sale.reply">商家回复：{{ sale.reply }}</p>
            </div>
            <div class="od-aftersale-side">
              <span class="price">¥{{ Number(sale.amount).toFixed(2) }}</span>
              <small>{{ String(sale.created_at).slice(0, 16).replace('T', ' ') }}</small>
            </div>
          </div>
        </section>
      </template>
    </main>
  </ShopLayout>
</template>
