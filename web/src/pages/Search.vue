<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import { api } from '../api'
import Icon from '../components/Icon.vue'
import ProductCard from '../components/ProductCard.vue'
import ShopLayout from '../components/ShopLayout.vue'

const route = useRoute()

const categories = ref([])
const brands = ref([])
const results = ref([])
const total = ref(0)
const page = ref(1)
const size = 20
const loading = ref(false)
const priceOrder = ref('price_asc')

const filters = reactive({
  q: route.query.q || '',
  category: '',
  brand: [],
  min: '',
  max: '',
  ordering: 'default',
  inStock: false,
})

const PRICE_PRESETS = [
  { label: '0-99 元', min: 0, max: 99 },
  { label: '100-499 元', min: 100, max: 499 },
  { label: '500-999 元', min: 500, max: 999 },
  { label: '1000-2999 元', min: 1000, max: 2999 },
  { label: '3000 元以上', min: 3000, max: '' },
]
const SORTS = [
  { key: 'default', label: '综合' },
  { key: 'sales', label: '销量' },
  { key: 'price', label: '价格' },
  { key: 'new', label: '新品' },
]

const activeCategory = computed(() => categories.value.find((c) => String(c.id) === String(filters.category)))
const activeBrands = computed(() => brands.value.filter((b) => filters.brand.includes(b.id)))
const pageCount = computed(() => Math.ceil(total.value / size) || 1)
const pages = computed(() => {
  const arr = []
  const start = Math.max(1, Math.min(page.value - 2, pageCount.value - 4))
  for (let i = start; i <= Math.min(pageCount.value, start + 4); i += 1) arr.push(i)
  return arr
})
const hasFilter = computed(
  () =>
    filters.category || filters.brand.length || filters.min !== '' || filters.max !== '' || filters.inStock
)

function params() {
  const p = {
    page: page.value,
    size,
    ordering: filters.ordering === 'price' ? priceOrder.value : filters.ordering,
  }
  if (filters.q) p.q = filters.q
  if (filters.category) p.category = filters.category
  if (filters.brand.length) p.brand = filters.brand.join(',')
  if (filters.min !== '') p.min_price = filters.min
  if (filters.max !== '') p.max_price = filters.max
  if (filters.inStock) p.in_stock = 1
  return p
}

async function fetchList() {
  loading.value = true
  try {
    const data = await api.get('/products/', params())
    results.value = data.results || []
    total.value = data.total || 0
  } finally {
    loading.value = false
  }
}

async function fetchBrands() {
  brands.value = (await api.get('/brands/', filters.category ? { category: filters.category } : {})) || []
}

function apply(reset = true) {
  if (reset) page.value = 1
  fetchList()
}

function chooseCategory(id) {
  filters.category = String(filters.category) === String(id) ? '' : id
  filters.brand = []
  fetchBrands().then(() => apply())
}

function toggleBrand(id) {
  const index = filters.brand.indexOf(id)
  if (index > -1) filters.brand.splice(index, 1)
  else filters.brand.push(id)
  apply()
}

function choosePrice(preset) {
  if (String(filters.min) === String(preset.min) && String(filters.max) === String(preset.max)) {
    filters.min = ''
    filters.max = ''
  } else {
    filters.min = preset.min
    filters.max = preset.max
  }
  apply()
}

function applyCustomPrice() {
  if (filters.min !== '' && filters.max !== '' && Number(filters.min) > Number(filters.max)) {
    const min = filters.min
    filters.min = filters.max
    filters.max = min
  }
  apply()
}

function changeSort(key) {
  if (key === 'price') {
    priceOrder.value = priceOrder.value === 'price_asc' ? 'price_desc' : 'price_asc'
    filters.ordering = 'price'
  } else {
    filters.ordering = key
  }
  apply()
}

function clearPrice() {
  filters.min = ''
  filters.max = ''
  apply()
}

function clearStock() {
  filters.inStock = false
  apply()
}

function clearAll() {
  filters.category = ''
  filters.brand = []
  filters.min = ''
  filters.max = ''
  filters.inStock = false
  apply()
}

function goPage(target) {
  if (target < 1 || target > pageCount.value) return
  page.value = target
  fetchList()
  window.scrollTo({ top: 220, behavior: 'smooth' })
}

watch(
  () => route.query.q,
  (q) => {
    const next = q || ''
    if (next !== filters.q) {
      filters.q = next
      page.value = 1
      fetchList()
    }
  }
)

onMounted(async () => {
  categories.value = (await api.get('/categories/')) || []
  if (route.query.category) filters.category = Number(route.query.category)
  await fetchBrands()
  fetchList()
})
</script>

<template>
  <ShopLayout>
    <main class="wrap search-page">
      <div class="breadcrumb">
        <RouterLink to="/">首页</RouterLink><span class="sep">›</span>
        <RouterLink :to="{ path: '/search', query: { q: filters.q } }">搜索结果</RouterLink>
        <span v-if="filters.q" class="sep">›</span>
        <span v-if="filters.q" class="current">{{ filters.q }}</span>
      </div>

      <section class="filter-panel">
        <div class="filter-row">
          <span class="filter-label">类目：</span>
          <div class="filter-values">
            <button :class="{ on: !filters.category }" @click="chooseCategory('')">全部</button>
            <button
              v-for="cat in categories"
              :key="cat.id"
              :class="{ on: String(filters.category) === String(cat.id) }"
              @click="chooseCategory(cat.id)"
            >
              {{ cat.name }}
            </button>
          </div>
        </div>

        <div class="filter-row">
          <span class="filter-label">品牌：</span>
          <div class="filter-values">
            <button
              v-for="brand in brands"
              :key="brand.id"
              :class="{ on: filters.brand.includes(brand.id) }"
              @click="toggleBrand(brand.id)"
            >
              {{ brand.name }}
            </button>
            <span v-if="!brands.length" class="filter-empty">该分类暂无品牌</span>
          </div>
        </div>

        <div class="filter-row">
          <span class="filter-label">价格：</span>
          <div class="filter-values price-filter">
            <button
              v-for="preset in PRICE_PRESETS"
              :key="preset.label"
              :class="{
                on: String(filters.min) === String(preset.min) && String(filters.max) === String(preset.max),
              }"
              @click="choosePrice(preset)"
            >
              {{ preset.label }}
            </button>
            <span class="price-inputs">
              <input v-model="filters.min" type="number" min="0" placeholder="最低价" />
              <i>—</i>
              <input v-model="filters.max" type="number" min="0" placeholder="最高价" />
              <button class="btn btn-plain btn-sm" @click="applyCustomPrice">确定</button>
            </span>
          </div>
        </div>

        <div v-if="hasFilter" class="filter-selected">
          <span class="filter-label">已选条件：</span>
          <div class="chips">
            <span v-if="activeCategory" class="chip">
              {{ activeCategory.name }}<i @click="chooseCategory('')">×</i>
            </span>
            <span v-for="brand in activeBrands" :key="brand.id" class="chip">
              {{ brand.name }}<i @click="toggleBrand(brand.id)">×</i>
            </span>
            <span v-if="filters.min !== '' || filters.max !== ''" class="chip">
              {{ filters.min || 0 }} - {{ filters.max || '不限' }} 元
              <i @click="clearPrice">×</i>
            </span>
            <span v-if="filters.inStock" class="chip"> 仅看有货<i @click="clearStock">×</i> </span>
            <button class="clear-all" @click="clearAll">清空筛选</button>
          </div>
        </div>
      </section>

      <section class="sort-bar">
        <div class="sort-items">
          <button
            v-for="sort in SORTS"
            :key="sort.key"
            class="sort-item"
            :class="{ on: filters.ordering === sort.key }"
            @click="changeSort(sort.key)"
          >
            {{ sort.label }}
            <span v-if="sort.key === 'price'" class="sort-arrows">
              <i :class="{ on: priceOrder === 'price_asc' }">▲</i
              ><i :class="{ on: priceOrder === 'price_desc' }">▼</i>
            </span>
          </button>
          <label class="stock-check">
            <input v-model="filters.inStock" type="checkbox" @change="apply()" />仅显示有货
          </label>
        </div>
        <div class="sort-meta">
          共 <b>{{ total }}</b> 件商品
          <span class="page-jump">
            <button :disabled="page <= 1" @click="goPage(page - 1)">‹</button>
            {{ page }}/{{ pageCount }}
            <button :disabled="page >= pageCount" @click="goPage(page + 1)">›</button>
          </span>
        </div>
      </section>

      <section class="search-result-panel">
        <div v-if="loading" class="loading">
          <div class="spinner" />
          正在为你筛选好物…
        </div>
        <template v-else>
          <div v-if="results.length" class="search-grid">
            <ProductCard v-for="product in results" :key="product.id" :product="product" size="lg" />
          </div>
          <div v-else class="empty">
            <div class="empty-icon"><Icon name="search" :size="42" /></div>
            <p>没有找到与「{{ filters.q || '当前条件' }}」相关的商品，换个关键词试试</p>
            <button class="btn btn-primary" @click="clearAll">清空筛选条件</button>
          </div>
        </template>
      </section>

      <div v-if="!loading && results.length" class="pager">
        <button :disabled="page <= 1" @click="goPage(1)">首页</button>
        <button :disabled="page <= 1" @click="goPage(page - 1)">上一页</button>
        <button v-for="p in pages" :key="p" :class="{ on: p === page }" @click="goPage(p)">{{ p }}</button>
        <button :disabled="page >= pageCount" @click="goPage(page + 1)">下一页</button>
        <button :disabled="page >= pageCount" @click="goPage(pageCount)">末页</button>
      </div>
    </main>
  </ShopLayout>
</template>
