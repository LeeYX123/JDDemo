<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { api } from '../api'
import Icon from '../components/Icon.vue'
import ProductImage from '../components/ProductImage.vue'
import ShopLayout from '../components/ShopLayout.vue'
import { useShopStore } from '../stores'

const shop = useShopStore()
const router = useRouter()

const addresses = ref([])
const selectedAddress = ref(null)
const remark = ref('')
const submitting = ref(false)
const showForm = ref(false)
const buyNow = ref(null)
const form = reactive({
  receiver: '',
  phone: '',
  province: '',
  city: '',
  district: '',
  detail: '',
  tag: '家',
  is_default: false,
})

onMounted(async () => {
  const raw = sessionStorage.getItem('jd_buy_now')
  if (raw) {
    try {
      buyNow.value = JSON.parse(raw)
    } catch {
      buyNow.value = null
    }
  }
  if (!buyNow.value) await shop.loadCart()
  addresses.value = (await api.get('/addresses/')) || []
  selectedAddress.value = addresses.value.find((a) => a.is_default) || addresses.value[0] || null
  if (!addresses.value.length) showForm.value = true
})

const groups = computed(() => {
  if (buyNow.value) {
    return [
      {
        id: buyNow.value.shop_id,
        name: buyNow.value.shop_name,
        items: [
          {
            id: `buy-${buyNow.value.sku_id}`,
            spu_id: buyNow.value.spu_id,
            title: buyNow.value.title,
            sku_name: buyNow.value.sku_name,
            price: buyNow.value.price,
            quantity: buyNow.value.quantity,
            image_seed: buyNow.value.image_seed,
          },
        ],
      },
    ]
  }
  const map = new Map()
  shop.selectedCart.forEach((item) => {
    if (!map.has(item.shop_id)) map.set(item.shop_id, { id: item.shop_id, name: item.shop_name, items: [] })
    map.get(item.shop_id).items.push(item)
  })
  return [...map.values()]
})

const subtotal = computed(() =>
  groups.value.reduce(
    (sum, group) => sum + group.items.reduce((s, item) => s + Number(item.price) * item.quantity, 0),
    0
  )
)
const freight = computed(() =>
  groups.value.reduce((sum, group) => {
    const amount = group.items.reduce((s, item) => s + Number(item.price) * item.quantity, 0)
    return sum + (amount >= 99 ? 0 : 8)
  }, 0)
)
const total = computed(() => subtotal.value + freight.value)
const totalCount = computed(() =>
  groups.value.reduce((n, group) => n + group.items.reduce((s, item) => s + item.quantity, 0), 0)
)

async function saveAddress() {
  if (!form.receiver || !form.phone || !form.province || !form.city || !form.detail) {
    shop.showToast('请完整填写收货人、手机号与详细地址')
    return
  }
  const created = await api.post('/addresses/', { ...form })
  addresses.value.unshift(created)
  selectedAddress.value = created
  showForm.value = false
  Object.assign(form, {
    receiver: '',
    phone: '',
    province: '',
    city: '',
    district: '',
    detail: '',
    tag: '家',
    is_default: false,
  })
  shop.showToast('地址已保存')
}

async function submit() {
  if (!selectedAddress.value) {
    shop.showToast('请选择收货地址')
    return
  }
  if (!groups.value.length) {
    shop.showToast('没有可结算的商品')
    return
  }
  submitting.value = true
  try {
    const payload = { address_id: selectedAddress.value.id, remark: remark.value }
    if (buyNow.value) {
      payload.sku_id = buyNow.value.sku_id
      payload.quantity = buyNow.value.quantity
    }
    const data = await api.post('/orders/', payload)
    sessionStorage.removeItem('jd_buy_now')
    if (!buyNow.value) await shop.loadCart()
    router.push(`/pay/${data.batch_no}`)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <ShopLayout>
    <main class="wrap checkout-page">
      <div class="checkout-steps">
        <div class="ck-step done"><i>1</i>填写核对订单信息</div>
        <div class="ck-line" />
        <div class="ck-step"><i>2</i>成功提交订单</div>
      </div>

      <section class="ck-block">
        <div class="ck-title">
          <h2>收货人信息</h2>
          <button class="link" @click="showForm = !showForm">{{ showForm ? '收起' : '使用新地址' }}</button>
        </div>

        <div class="address-list">
          <button
            v-for="address in addresses"
            :key="address.id"
            class="address-card"
            :class="{ on: selectedAddress?.id === address.id }"
            @click="selectedAddress = address"
          >
            <div class="addr-top">
              <b>{{ address.receiver }}</b>
              <span>{{ address.phone }}</span>
              <i v-if="address.is_default" class="tag">默认</i>
            </div>
            <p>{{ address.full_text }}</p>
            <em v-if="address.tag">{{ address.tag }}</em>
          </button>
          <button v-if="!showForm" class="address-card add" @click="showForm = true">＋ 新增收货地址</button>
        </div>

        <div v-if="showForm" class="address-form">
          <div class="form-row">
            <div class="form-item">
              <label class="form-label">收货人</label>
              <input v-model="form.receiver" class="form-input" placeholder="请输入姓名" />
            </div>
            <div class="form-item">
              <label class="form-label">手机号</label>
              <input v-model="form.phone" class="form-input" placeholder="11 位手机号" maxlength="11" />
            </div>
            <div class="form-item">
              <label class="form-label">标签</label>
              <select v-model="form.tag" class="form-input">
                <option>家</option>
                <option>公司</option>
                <option>学校</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-item">
              <label class="form-label">省份</label>
              <input v-model="form.province" class="form-input" placeholder="如 北京市" />
            </div>
            <div class="form-item">
              <label class="form-label">城市</label>
              <input v-model="form.city" class="form-input" placeholder="如 北京市" />
            </div>
            <div class="form-item">
              <label class="form-label">区县</label>
              <input v-model="form.district" class="form-input" placeholder="如 朝阳区" />
            </div>
          </div>
          <div class="form-item">
            <label class="form-label">详细地址</label>
            <input v-model="form.detail" class="form-input" placeholder="街道、门牌号、楼层等" />
          </div>
          <div class="form-foot">
            <label class="checkbox"><input v-model="form.is_default" type="checkbox" />设为默认地址</label>
            <button class="btn btn-primary" @click="saveAddress">保存地址</button>
          </div>
        </div>
      </section>

      <section class="ck-block">
        <div class="ck-title">
          <h2>商品清单</h2>
          <span class="ck-tip">按店铺拆单，支持分别发货</span>
        </div>

        <div v-if="!groups.length" class="empty">
          <p>没有待结算的商品</p>
          <RouterLink to="/cart" class="btn btn-primary">返回购物车</RouterLink>
        </div>

        <div v-for="group in groups" :key="group.id" class="ck-shop">
          <div class="ck-shop-head">
            <Icon name="bag" :size="14" /><b>{{ group.name }}</b>
            <span>京东物流配送</span>
          </div>
          <div v-for="item in group.items" :key="item.id" class="ck-item">
            <ProductImage :seed="item.image_seed" size="sm" :title="item.title" />
            <div class="ck-item-info">
              <RouterLink :to="`/item/${item.spu_id}`" class="ck-item-title">{{ item.title }}</RouterLink>
              <p class="ck-item-spec">{{ item.sku_name }}</p>
              <span class="tag tag-plain">7 天无理由</span>
            </div>
            <div class="ck-item-price">
              <span class="price price-sm"
                ><span class="symbol">¥</span
                ><span class="price-int">{{ Number(item.price).toFixed(2) }}</span></span
              >
              <span class="ck-qty">× {{ item.quantity }}</span>
            </div>
            <div class="ck-item-sum">
              <span class="price"
                ><span class="symbol">¥</span
                ><span class="price-int">{{ (Number(item.price) * item.quantity).toFixed(2) }}</span></span
              >
            </div>
          </div>
          <div class="ck-shop-foot">
            <span
              >运费：{{
                group.items.reduce((s, i) => s + Number(i.price) * i.quantity, 0) >= 99 ? '免运费' : '¥8.00'
              }}</span
            >
            <span>支付方式：在线支付</span>
          </div>
        </div>
      </section>

      <section class="ck-block">
        <div class="ck-title"><h2>订单备注</h2></div>
        <input
          v-model="remark"
          class="form-input remark-input"
          maxlength="120"
          placeholder="选填，可填写配送时间、发票等要求（120 字以内）"
        />
      </section>

      <section class="ck-summary">
        <div class="ck-summary-row">
          <span>商品件数：</span><b>{{ totalCount }} 件</b>
        </div>
        <div class="ck-summary-row">
          <span>商品总价：</span><b>¥{{ subtotal.toFixed(2) }}</b>
        </div>
        <div class="ck-summary-row">
          <span>运费：</span><b>{{ freight ? `¥${freight.toFixed(2)}` : '免运费' }}</b>
        </div>
        <div class="ck-summary-row total">
          <span>应付总额：</span>
          <span class="price price-lg"
            ><span class="symbol">¥</span><span class="price-int">{{ total.toFixed(2) }}</span></span
          >
        </div>
        <div class="ck-address-preview">
          寄送至：{{ selectedAddress ? selectedAddress.full_text : '请选择收货地址' }} <br />收货人：{{
            selectedAddress ? `${selectedAddress.receiver} ${selectedAddress.phone}` : '—'
          }}
        </div>
        <div class="ck-submit">
          <RouterLink to="/cart" class="back-cart">返回购物车</RouterLink>
          <button class="btn btn-primary btn-lg" :disabled="submitting || !groups.length" @click="submit">
            {{ submitting ? '提交中…' : '提交订单' }}
          </button>
        </div>
      </section>
    </main>
  </ShopLayout>
</template>
