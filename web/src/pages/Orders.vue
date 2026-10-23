<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { api } from '../api'
import Icon from '../components/Icon.vue'
import ProductImage from '../components/ProductImage.vue'
import ShopLayout from '../components/ShopLayout.vue'
import { useShopStore } from '../stores'

const router = useRouter()
const shop = useShopStore()

const TABS = [
  { key: '', label: '全部订单' },
  { key: 'pending_pay', label: '待付款' },
  { key: 'paid', label: '待发货' },
  { key: 'shipped', label: '待收货' },
  { key: 'completed', label: '已完成' },
  { key: 'cancelled', label: '已取消' },
]

const tab = ref('')
const orders = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)

const reviewOrder = ref(null)
const reviewForm = reactive({ rating: 5, content: '' })
const afterOrder = ref(null)
const afterForm = reactive({ order_item_id: '', type: 'refund', reason: '商品与描述不符', description: '' })

const pageCount = computed(() => Math.ceil(total.value / 10) || 1)

async function load() {
  loading.value = true
  try {
    const data = await api.get('/orders/', { page: page.value, size: 10, status: tab.value || undefined })
    orders.value = data.results || []
    total.value = data.total || 0
  } finally {
    loading.value = false
  }
}

function changeTab(key) {
  tab.value = key
  page.value = 1
  load()
}

function goPage(next) {
  if (next < 1 || next > pageCount.value) return
  page.value = next
  load()
}

async function cancel(order) {
  if (!window.confirm('确定要取消该订单吗？取消后库存将自动回滚。')) return
  await api.post(`/orders/${order.order_no}/cancel/`, { reason: '用户主动取消' })
  shop.showToast('订单已取消')
  load()
}

function pay(order) {
  router.push(`/pay/${order.batch_no || order.order_no}`)
}

async function confirm(order) {
  if (!window.confirm('确认已收到商品吗？')) return
  await api.post(`/orders/${order.order_no}/confirm/`)
  shop.showToast('已确认收货')
  load()
}

function openReview(order) {
  reviewOrder.value = order
  reviewForm.rating = 5
  reviewForm.content = ''
}

async function submitReview() {
  await api.post('/reviews/', {
    order_no: reviewOrder.value.order_no,
    rating: reviewForm.rating,
    content: reviewForm.content || '商品不错，物流很快，值得推荐。',
  })
  shop.showToast('评价成功，感谢你的分享')
  reviewOrder.value = null
  load()
}

function openAfterSale(order) {
  afterOrder.value = order
  afterForm.order_item_id = order.items[0]?.id || ''
  afterForm.type = 'refund'
  afterForm.reason = '商品与描述不符'
  afterForm.description = ''
}

async function submitAfterSale() {
  await api.post('/aftersales/', { ...afterForm })
  shop.showToast('售后申请已提交，等待商家处理')
  afterOrder.value = null
  load()
}

function itemLink(item) {
  return item.spu_id ? `/item/${item.spu_id}` : '#'
}

onMounted(load)
</script>

<template>
  <ShopLayout>
    <main class="wrap orders-page">
      <div class="orders-head">
        <h1>我的订单</h1>
        <RouterLink to="/user" class="orders-help">订单帮助</RouterLink>
      </div>

      <div class="order-tabs">
        <button
          v-for="item in TABS"
          :key="item.key"
          :class="{ on: tab === item.key }"
          @click="changeTab(item.key)"
        >
          {{ item.label }}
        </button>
        <span class="order-total">共 {{ total }} 笔订单</span>
      </div>

      <div v-if="loading" class="loading">
        <div class="spinner" />
        正在加载订单…
      </div>

      <template v-else>
        <article v-for="order in orders" :key="order.id" class="order-card">
          <header class="order-card-head">
            <span class="oc-time">{{ String(order.created_at).replace('T', ' ').slice(0, 16) }}</span>
            <span class="oc-no">订单号：{{ order.order_no }}</span>
            <span class="oc-shop">{{ (order.shop_names || []).join(' / ') }}</span>
            <span class="oc-status" :class="`st-${order.status}`">{{ order.status_label }}</span>
          </header>

          <div class="order-card-body">
            <div class="order-items">
              <div v-for="item in order.items" :key="item.id" class="order-item">
                <RouterLink :to="itemLink(item)">
                  <ProductImage :seed="item.image_seed" size="sm" :title="item.title_snapshot" />
                </RouterLink>
                <div class="oi-info">
                  <RouterLink :to="itemLink(item)" class="oi-title">{{ item.title_snapshot }}</RouterLink>
                  <p class="oi-spec">{{ Object.values(item.specs_snapshot || {}).join(' / ') }}</p>
                  <span v-if="item.aftersale_status" class="tag tag-gray"
                    >售后：{{ item.aftersale_status }}</span
                  >
                </div>
                <div class="oi-price">
                  ¥{{ Number(item.price_snapshot).toFixed(2) }} × {{ item.quantity }}
                </div>
              </div>
            </div>

            <div class="order-side">
              <div class="os-total">
                <span>实付款</span>
                <span class="price"
                  ><span class="symbol">¥</span
                  ><span class="price-int">{{ Number(order.total).toFixed(2) }}</span></span
                >
              </div>
              <p class="os-freight">含运费 ¥{{ Number(order.freight).toFixed(2) }}</p>
              <div class="os-actions">
                <button v-if="order.can_cancel" class="btn btn-plain btn-sm" @click="cancel(order)">
                  取消订单
                </button>
                <button v-if="order.can_pay" class="btn btn-primary btn-sm" @click="pay(order)">
                  立即付款
                </button>
                <button v-if="order.can_confirm" class="btn btn-primary btn-sm" @click="confirm(order)">
                  确认收货
                </button>
                <button v-if="order.can_review" class="btn btn-ghost btn-sm" @click="openReview(order)">
                  评价晒单
                </button>
                <button
                  v-if="['paid', 'shipped', 'completed'].includes(order.status)"
                  class="btn btn-plain btn-sm"
                  @click="openAfterSale(order)"
                >
                  申请售后
                </button>
                <RouterLink :to="`/orders/${order.order_no}`" class="btn btn-plain btn-sm">
                  订单详情
                </RouterLink>
              </div>
            </div>
          </div>

          <footer v-if="order.tracking_no" class="order-card-foot">
            <Icon name="truck" :size="14" />
            {{ order.tracking_company }}：{{ order.tracking_no }}
            <span class="oc-hint">商品正在配送中</span>
          </footer>
        </article>

        <div v-if="!orders.length" class="empty panel orders-empty">
          <div class="empty-icon"><Icon name="bag" :size="44" /></div>
          <p>还没有相关订单，去挑点好物吧</p>
          <RouterLink to="/" class="btn btn-primary">去逛逛</RouterLink>
        </div>

        <div v-if="total > 10" class="pager">
          <button :disabled="page <= 1" @click="goPage(page - 1)">上一页</button>
          <span class="page-text">第 {{ page }} / {{ pageCount }} 页</span>
          <button :disabled="page >= pageCount" @click="goPage(page + 1)">下一页</button>
        </div>
      </template>

      <!-- 评价弹窗 -->
      <div v-if="reviewOrder" class="modal-mask" @click.self="reviewOrder = null">
        <div class="modal-card">
          <div class="modal-head">
            <h3>评价晒单</h3>
            <button @click="reviewOrder = null"><Icon name="close" :size="16" /></button>
          </div>
          <div class="modal-body">
            <p class="modal-tip">订单号：{{ reviewOrder.order_no }}</p>
            <div class="star-picker">
              <span
                v-for="star in 5"
                :key="star"
                :class="{ on: star <= reviewForm.rating }"
                @click="reviewForm.rating = star"
                >★</span
              >
              <em>{{ ['很差', '一般', '还行', '满意', '非常满意'][reviewForm.rating - 1] }}</em>
            </div>
            <textarea
              v-model="reviewForm.content"
              class="form-input"
              placeholder="说说商品的使用感受，帮助更多人挑选（默认好评）"
            />
          </div>
          <div class="modal-foot">
            <button class="btn btn-plain" @click="reviewOrder = null">取消</button>
            <button class="btn btn-primary" @click="submitReview">提交评价</button>
          </div>
        </div>
      </div>

      <!-- 售后弹窗 -->
      <div v-if="afterOrder" class="modal-mask" @click.self="afterOrder = null">
        <div class="modal-card">
          <div class="modal-head">
            <h3>申请售后</h3>
            <button @click="afterOrder = null"><Icon name="close" :size="16" /></button>
          </div>
          <div class="modal-body">
            <div class="form-item">
              <label class="form-label">选择商品</label>
              <select v-model="afterForm.order_item_id" class="form-input">
                <option v-for="item in afterOrder.items" :key="item.id" :value="item.id">
                  {{ item.title_snapshot }}
                </option>
              </select>
            </div>
            <div class="form-item">
              <label class="form-label">售后类型</label>
              <select v-model="afterForm.type" class="form-input">
                <option value="refund">仅退款</option>
                <option value="return">退货退款</option>
              </select>
            </div>
            <div class="form-item">
              <label class="form-label">申请原因</label>
              <select v-model="afterForm.reason" class="form-input">
                <option>商品与描述不符</option>
                <option>商品破损或缺件</option>
                <option>尺寸 / 颜色不合适</option>
                <option>七天无理由退货</option>
                <option>其他原因</option>
              </select>
            </div>
            <div class="form-item">
              <label class="form-label">补充说明</label>
              <textarea
                v-model="afterForm.description"
                class="form-input"
                placeholder="选填，描述具体情况有助于更快处理"
              />
            </div>
          </div>
          <div class="modal-foot">
            <button class="btn btn-plain" @click="afterOrder = null">取消</button>
            <button class="btn btn-primary" @click="submitAfterSale">提交申请</button>
          </div>
        </div>
      </div>
    </main>
  </ShopLayout>
</template>
