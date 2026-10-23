<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import Icon from '../components/Icon.vue'
import ProductImage from '../components/ProductImage.vue'
import ShopLayout from '../components/ShopLayout.vue'
import { useShopStore } from '../stores'

const shop = useShopStore()
const router = useRouter()
const removing = ref(false)

onMounted(() => shop.loadCart())

const validItems = computed(() => shop.cart.filter((item) => item.valid))
const invalidItems = computed(() => shop.cart.filter((item) => !item.valid))
const groups = computed(() => {
  const map = new Map()
  validItems.value.forEach((item) => {
    if (!map.has(item.shop_id)) {
      map.set(item.shop_id, { id: item.shop_id, name: item.shop_name, items: [] })
    }
    map.get(item.shop_id).items.push(item)
  })
  return [...map.values()]
})

const allChecked = computed({
  get: () => validItems.value.length > 0 && validItems.value.every((item) => item.selected),
  set: (value) => shop.toggleAll(value),
})

function groupChecked(group) {
  return group.items.every((item) => item.selected)
}

async function toggleGroup(group, checked) {
  await Promise.all(group.items.map((item) => shop.updateCart(item.id, { selected: checked })))
}

function changeQty(item, delta) {
  const next = Math.min(item.stock, Math.max(1, item.quantity + delta))
  if (next !== item.quantity) shop.updateCart(item.id, { quantity: next })
}

function inputQty(item, event) {
  const value = Math.min(item.stock, Math.max(1, Number(event.target.value) || 1))
  event.target.value = value
  shop.updateCart(item.id, { quantity: value })
}

function removeItem(item) {
  if (window.confirm(`确定要删除「${item.title}」吗？`)) shop.removeCart(item.id)
}

async function removeSelected() {
  if (!shop.selectedCount) return shop.showToast('请先选择商品')
  if (!window.confirm(`确定删除选中的 ${shop.selectedCount} 件商品吗？`)) return
  removing.value = true
  try {
    await shop.removeSelected()
  } finally {
    removing.value = false
  }
}

function checkout() {
  if (!shop.selectedCount) return shop.showToast('请先选择要结算的商品')
  router.push('/checkout')
}
</script>

<template>
  <ShopLayout>
    <main class="wrap cart-page">
      <div class="cart-head">
        <h1>我的购物车</h1>
        <span>共 {{ shop.cartCount }} 件商品，已选择 {{ shop.selectedCount }} 件</span>
      </div>

      <div v-if="!shop.cart.length" class="cart-empty panel">
        <div class="empty">
          <div class="empty-icon"><Icon name="cart" :size="46" /></div>
          <p>购物车还是空的，去挑点好东西吧</p>
          <RouterLink to="/" class="btn btn-primary">去逛逛</RouterLink>
        </div>
      </div>

      <template v-else>
        <div class="cart-table-head">
          <label class="check-all"><input v-model="allChecked" type="checkbox" />全选</label>
          <span class="col-goods">商品信息</span>
          <span class="col-price">单价</span>
          <span class="col-qty">数量</span>
          <span class="col-sum">小计</span>
          <span class="col-op">操作</span>
        </div>

        <section v-for="group in groups" :key="group.id" class="cart-group panel">
          <div class="group-head">
            <label class="check-all">
              <input
                type="checkbox"
                :checked="groupChecked(group)"
                @change="toggleGroup(group, $event.target.checked)"
              />
              <Icon name="bag" :size="14" />
              <b>{{ group.name }}</b>
            </label>
            <span class="group-tip">满 99 元免运费</span>
          </div>

          <div v-for="item in group.items" :key="item.id" class="cart-row">
            <label class="check-cell">
              <input
                type="checkbox"
                :checked="item.selected"
                @change="shop.updateCart(item.id, { selected: $event.target.checked })"
              />
            </label>
            <div class="goods-cell">
              <RouterLink :to="`/item/${item.spu_id}`">
                <ProductImage :seed="item.image_seed" size="sm" :title="item.title" />
              </RouterLink>
              <div class="goods-info">
                <RouterLink :to="`/item/${item.spu_id}`" class="goods-title">{{ item.title }}</RouterLink>
                <p class="goods-spec">{{ item.sku_name }}</p>
                <div class="goods-tags">
                  <span class="tag tag-plain">7 天无理由</span>
                  <span class="tag tag-gray">京东物流</span>
                </div>
              </div>
            </div>
            <div class="price-cell">
              <span class="price price-sm"
                ><span class="symbol">¥</span
                ><span class="price-int">{{ Number(item.price).toFixed(2) }}</span></span
              >
            </div>
            <div class="qty-cell">
              <div class="qty-box">
                <button :disabled="item.quantity <= 1" @click="changeQty(item, -1)">−</button>
                <input
                  :value="item.quantity"
                  type="number"
                  min="1"
                  :max="item.stock"
                  @change="inputQty(item, $event)"
                />
                <button :disabled="item.quantity >= item.stock" @click="changeQty(item, 1)">＋</button>
              </div>
              <span v-if="item.stock <= 5" class="stock-warn">仅剩 {{ item.stock }} 件</span>
            </div>
            <div class="sum-cell">
              <span class="price"
                ><span class="symbol">¥</span
                ><span class="price-int">{{ (Number(item.price) * item.quantity).toFixed(2) }}</span></span
              >
            </div>
            <div class="op-cell">
              <a @click="removeItem(item)">删除</a>
            </div>
          </div>
        </section>

        <section v-if="invalidItems.length" class="cart-group invalid panel">
          <div class="group-head">
            <b>失效商品 {{ invalidItems.length }} 件</b>
            <span class="group-tip">已下架或无货</span>
          </div>
          <div v-for="item in invalidItems" :key="item.id" class="cart-row">
            <label class="check-cell"><span class="invalid-flag">失效</span></label>
            <div class="goods-cell">
              <ProductImage :seed="item.image_seed" size="sm" :title="item.title" />
              <div class="goods-info">
                <span class="goods-title">{{ item.title }}</span>
                <p class="goods-spec">{{ item.sku_name }}</p>
              </div>
            </div>
            <div class="price-cell">{{ item.stock ? '已下架' : '无货' }}</div>
            <div class="qty-cell" />
            <div class="sum-cell" />
            <div class="op-cell"><a @click="removeItem(item)">删除</a></div>
          </div>
        </section>

        <div class="cart-settle">
          <div class="settle-inner">
            <label class="check-all"><input v-model="allChecked" type="checkbox" />全选</label>
            <button class="settle-link" @click="removeSelected">删除选中</button>
            <RouterLink to="/" class="settle-link">继续购物</RouterLink>
            <div class="settle-right">
              <span class="settle-count"
                >已选 <b>{{ shop.selectedCount }}</b> 件商品</span
              >
              <span class="settle-total">
                合计（不含运费）：
                <span class="price price-lg"
                  ><span class="symbol">¥</span
                  ><span class="price-int">{{ shop.cartTotal.toFixed(2) }}</span></span
                >
              </span>
              <button class="btn btn-primary btn-lg settle-btn" :disabled="removing" @click="checkout">
                去结算
              </button>
            </div>
          </div>
        </div>
      </template>
    </main>
  </ShopLayout>
</template>
