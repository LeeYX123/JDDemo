<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api } from '../api'
import Icon from '../components/Icon.vue'
import ItemTabs from '../components/ItemTabs.vue'
import ProductCard from '../components/ProductCard.vue'
import ProductImage from '../components/ProductImage.vue'
import ShopLayout from '../components/ShopLayout.vue'
import { useShopStore } from '../stores'

const route = useRoute()
const router = useRouter()
const shop = useShopStore()

const product = ref(null)
const loading = ref(true)
const tab = ref('detail')
const quantity = ref(1)
const activeThumb = ref(0)
const selected = reactive({})
const adding = ref(false)

const thumbs = computed(() => {
  const seed = product.value?.image_seed || 1
  return [0, 1, 2, 3, 4].map((i) => seed + i)
})

const specKeys = computed(() => {
  const keys = new Set()
  ;(product.value?.skus || []).forEach((sku) => Object.keys(sku.specs || {}).forEach((k) => keys.add(k)))
  return [...keys]
})

function specValues(key) {
  const values = []
  ;(product.value?.skus || []).forEach((sku) => {
    const value = sku.specs?.[key]
    if (value && !values.includes(value)) values.push(value)
  })
  return values
}

const currentSku = computed(() => {
  const skus = product.value?.skus || []
  if (!skus.length) return null
  const hit = skus.find((sku) => specKeys.value.every((key) => sku.specs?.[key] === selected[key]))
  return hit || skus[0]
})

const price = computed(() => Number(currentSku.value?.price || 0).toFixed(2))
const marketPrice = computed(() => Number(currentSku.value?.market_price || 0).toFixed(2))
const stock = computed(() => currentSku.value?.stock || 0)

function pickSpec(key, value) {
  const candidate = { ...selected, [key]: value }
  const hit = (product.value?.skus || []).find((sku) =>
    specKeys.value.every((k) => sku.specs?.[k] === candidate[k])
  )
  if (hit) {
    Object.assign(selected, candidate)
    if (quantity.value > hit.stock) quantity.value = Math.max(1, hit.stock)
  }
}

function changeQty(delta) {
  const next = quantity.value + delta
  quantity.value = Math.max(1, Math.min(stock.value || 1, next))
}

async function load(id) {
  loading.value = true
  try {
    product.value = await api.get(`/products/${id}/`)
    const first = product.value.skus?.[0]
    Object.keys(selected).forEach((key) => delete selected[key])
    if (first) Object.assign(selected, first.specs || {})
    quantity.value = 1
    activeThumb.value = 0
    tab.value = 'detail'
  } finally {
    loading.value = false
  }
}

function requireLogin() {
  if (localStorage.getItem('jd_access')) return true
  router.push({ path: '/login', query: { next: route.fullPath } })
  return false
}

function flyToCart() {
  const target = document.getElementById('cart-entry')
  if (!target) return
  const end = target.getBoundingClientRect()
  const ball = document.createElement('span')
  ball.className = 'fly-ball'
  Object.assign(ball.style, { left: `${end.left + 18}px`, top: `${end.top + 6}px` })
  document.body.appendChild(ball)
  ball.animate(
    [
      { transform: 'translate(0, 0) scale(1.6)', opacity: 1 },
      {
        transform: `translate(-${Math.max(120, end.left - 260)}px, 60px) scale(.9)`,
        opacity: 1,
        offset: 0.55,
      },
      { transform: 'translate(0, 0) scale(.2)', opacity: 0.2 },
    ],
    { duration: 700, easing: 'cubic-bezier(.35,.05,.65,.95)' }
  ).onfinish = () => ball.remove()
}

async function addCart(goCart = false) {
  if (!requireLogin() || !currentSku.value) return
  if (!stock.value) {
    shop.showToast('该规格暂时无货')
    return
  }
  adding.value = true
  try {
    await shop.addCart(currentSku.value.id, quantity.value)
    flyToCart()
    if (goCart) router.push('/cart')
  } finally {
    adding.value = false
  }
}

function buyNow() {
  if (!requireLogin() || !currentSku.value) return
  sessionStorage.setItem(
    'jd_buy_now',
    JSON.stringify({
      sku_id: currentSku.value.id,
      quantity: quantity.value,
      title: product.value.title,
      price: currentSku.value.price,
      sku_name: currentSku.value.name,
      image_seed: product.value.image_seed,
      shop_name: product.value.shop_name,
      shop_id: product.value.shop_id,
      spu_id: product.value.id,
    })
  )
  router.push('/checkout')
}

watch(
  () => route.params.id,
  (id) => id && load(id)
)

load(route.params.id)
</script>

<template>
  <ShopLayout>
    <main class="wrap item-page">
      <div class="breadcrumb">
        <RouterLink to="/">首页</RouterLink>
        <template v-for="node in product?.category_path || []" :key="node.id">
          <span class="sep">›</span>
          <RouterLink :to="{ path: '/search', query: { category: node.id } }">{{ node.name }}</RouterLink>
        </template>
        <span class="sep">›</span>
        <span class="current">{{ product?.title }}</span>
      </div>

      <div v-if="loading" class="loading">
        <div class="spinner" />
        正在加载商品…
      </div>

      <template v-else-if="product">
        <section class="item-main">
          <div class="gallery">
            <div class="gallery-main">
              <ProductImage :seed="thumbs[activeThumb]" size="xl" :title="product.title" />
              <span class="gallery-hint">图片为演示占位图</span>
            </div>
            <div class="gallery-thumbs">
              <button
                v-for="(seed, i) in thumbs"
                :key="seed"
                :class="{ on: activeThumb === i }"
                @click="activeThumb = i"
              >
                <ProductImage :seed="seed" size="thumb" :title="product.title" />
              </button>
            </div>
            <div class="gallery-actions">
              <button @click="shop.showToast('已收藏商品')"><Icon name="heart" :size="14" />收藏</button>
              <button @click="shop.showToast('已分享商品链接')">
                <Icon name="comment" :size="14" />分享
              </button>
            </div>
          </div>

          <div class="item-info">
            <h1 class="item-title">{{ product.title }}</h1>
            <p class="item-sub">{{ product.subtitle }}</p>

            <div class="price-box">
              <div class="price-line">
                <span class="label">京东价</span>
                <span class="price price-lg"
                  ><span class="symbol">¥</span><span class="price-int">{{ price }}</span></span
                >
                <span class="price-origin">¥{{ marketPrice }}</span>
                <span class="discount-tip"
                  >已优惠 {{ (Number(marketPrice) - Number(price)).toFixed(2) }} 元</span
                >
              </div>
              <div class="info-line">
                <span class="label">促销</span>
                <span class="tag">满减</span>
                <span class="promo-text">满 99 减 20，满 499 减 50，可与优惠券叠加</span>
              </div>
              <div class="info-line">
                <span class="label">累计评价</span>
                <a class="count-link" @click="tab = 'reviews'">{{ product.review_count }} 条评价</a>
                <span class="divider" />
                <span class="label">销量</span>
                <span>{{ product.sales }} 件</span>
              </div>
              <div class="info-line">
                <span class="label">配送至</span>
                <span class="addr">北京市朝阳区</span>
                <span class="stock-tip" :class="{ danger: !stock }">
                  {{ stock ? `现货，库存 ${stock} 件` : '暂时无货' }}
                </span>
              </div>
              <div class="info-line">
                <span class="label">服务</span>
                <span class="service-tags">
                  <i v-for="tag in product.service_list" :key="tag">{{ tag }}</i>
                </span>
              </div>
            </div>

            <div class="sku-area">
              <div v-for="key in specKeys" :key="key" class="sku-row">
                <span class="label">{{ key }}</span>
                <div class="sku-values">
                  <button
                    v-for="value in specValues(key)"
                    :key="value"
                    :class="{ on: selected[key] === value }"
                    @click="pickSpec(key, value)"
                  >
                    {{ value }}
                  </button>
                </div>
              </div>
              <div class="sku-row">
                <span class="label">数量</span>
                <div class="qty-box">
                  <button :disabled="quantity <= 1" @click="changeQty(-1)">−</button>
                  <input
                    v-model.number="quantity"
                    type="number"
                    min="1"
                    :max="stock"
                    @change="changeQty(0)"
                  />
                  <button :disabled="quantity >= stock" @click="changeQty(1)">＋</button>
                </div>
                <span class="stock-tip">最多购买 {{ stock }} 件</span>
              </div>
            </div>

            <div class="buy-actions">
              <button
                class="btn btn-ghost btn-lg add-cart"
                :disabled="adding || !stock"
                @click="addCart(false)"
              >
                <Icon name="cart" :size="18" />加入购物车
              </button>
              <button class="btn btn-primary btn-lg" :disabled="!stock" @click="buyNow">立即购买</button>
              <button class="btn btn-plain btn-lg" @click="addCart(true)">去购物车结算</button>
            </div>

            <div class="shop-card">
              <div class="shop-logo">{{ product.shop?.name?.slice(0, 1) || '京' }}</div>
              <div class="shop-info">
                <b>{{ product.shop?.name || '京东自营' }}</b>
                <span>店铺评分 {{ product.shop?.rating || '4.9' }} · 正品保障</span>
              </div>
              <button class="btn btn-plain btn-sm" @click="shop.showToast('客服小京为您服务')">
                联系客服
              </button>
              <RouterLink
                class="btn btn-ghost btn-sm"
                :to="{ path: '/search', query: { shop: product.shop_id } }"
              >
                进店逛逛
              </RouterLink>
            </div>
          </div>
        </section>

        <ItemTabs v-model="tab" :product="product" :spec-keys="specKeys" :spec-values="specValues" />

        <section v-if="product.related?.length" class="related">
          <div class="section-head">
            <h2>看了又看</h2>
            <RouterLink class="more" to="/search">更多好物 ›</RouterLink>
          </div>
          <div class="related-grid">
            <ProductCard v-for="item in product.related" :key="item.id" :product="item" />
          </div>
        </section>
      </template>
    </main>
  </ShopLayout>
</template>
