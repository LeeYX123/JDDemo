<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import PageHead from '../../components/PageHead.vue'
import StatCard from '../../components/StatCard.vue'
import TrendChart from '../../components/TrendChart.vue'
import { api } from '../../api'
import { statusLabel } from '../../menus'

const router = useRouter()
const loading = ref(true)
const data = ref({})

const stats = computed(() => data.value.stats || {})
const trend = computed(() => data.value.trend || [])
const ranking = computed(() => data.value.shop_ranking || [])
const categories = computed(() => data.value.categories || [])
const recent = computed(() => data.value.recent_orders || [])

const maxRankGmv = computed(() => Math.max(...ranking.value.map((item) => item.gmv), 1))
const maxCatValue = computed(() => Math.max(...categories.value.map((item) => item.value), 1))
const todoTotal = computed(
  () =>
    Number(stats.value.pending_products || 0) +
    Number(stats.value.pending_shops || 0) +
    Number(stats.value.pending_aftersales || 0)
)

const money = (value) => Number(value || 0).toFixed(2)
const compact = (value) => {
  const n = Number(value || 0)
  if (n >= 10000) return `${(n / 10000).toFixed(n >= 100000 ? 0 : 1)}万`
  return n.toFixed(0)
}

const TODOS = computed(() => [
  { label: '商品待审核', value: stats.value.pending_products || 0, path: '/console/products?status=pending' },
  { label: '商家待审核', value: stats.value.pending_shops || 0, path: '/console/shops' },
  { label: '售后待处理', value: stats.value.pending_aftersales || 0, path: '/console/orders' },
])

async function load() {
  loading.value = true
  try {
    data.value = (await api.get('/console/dashboard/')) || {}
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div v-loading="loading">
    <PageHead title="平台数据看板" desc="全站交易、用户与店铺概览，含待办审核提醒">
      <template #actions>
        <el-button @click="load">刷新数据</el-button>
        <el-button type="primary" @click="router.push('/console/content')">内容运营</el-button>
      </template>
    </PageHead>

    <div class="stat-grid" style="grid-template-columns: repeat(6, minmax(0, 1fr))">
      <StatCard label="平台 GMV" unit="¥" :value="money(stats.gmv)" hint="有效订单口径" />
      <StatCard
        label="今日 GMV"
        unit="¥"
        :value="money(stats.today_gmv)"
        :hint="`今日 ${stats.today_orders || 0} 单`"
      />
      <StatCard label="订单总量" :value="stats.orders ?? 0" hint="含全部状态" />
      <StatCard label="买家数" :value="stats.buyers ?? 0" hint="注册买家账号" />
      <StatCard label="入驻店铺" :value="stats.shops ?? 0" hint="含待审核" />
      <StatCard
        label="待办审核"
        :value="todoTotal"
        :hint="todoTotal ? '点击下方处理' : '全部已处理'"
        :hint-type="todoTotal ? 'warn' : ''"
      />
    </div>

    <div class="dash-grid">
      <section class="panel">
        <div class="panel-head">
          <h3>近 7 日平台 GMV 趋势</h3>
          <span class="tip">单位：元</span>
          <div class="right legend"><i style="background: #1d64d8" />GMV</div>
        </div>
        <div class="panel-body">
          <TrendChart
            :data="trend"
            value-key="gmv"
            label-key="date"
            type="line"
            color="#1d64d8"
            :height="252"
            :formatter="compact"
          />
        </div>
      </section>

      <section class="panel">
        <div class="panel-head">
          <h3>待办事项</h3>
          <span class="right tip">共 {{ todoTotal }} 项</span>
        </div>
        <div class="panel-body">
          <div class="rank-list">
            <div
              v-for="todo in TODOS"
              :key="todo.label"
              class="rank-row"
              style="cursor: pointer"
              @click="router.push(todo.path)"
            >
              <span class="rank-no" :class="{ top1: todo.value > 0 }">!</span>
              <span class="rank-name">{{ todo.label }}</span>
              <span class="rank-value"
                ><b>{{ todo.value }}</b> 项</span
              >
            </div>
          </div>

          <h4 style="margin: 22px 0 10px; font-size: 13px">经营概览</h4>
          <div class="rank-list">
            <div class="rank-row">
              <span class="rank-no">货</span>
              <span class="rank-name">全站商品数</span>
              <span class="rank-value"
                ><b>{{ stats.products ?? 0 }}</b> 个</span
              >
            </div>
            <div class="rank-row">
              <span class="rank-no">店</span>
              <span class="rank-name">在营店铺</span>
              <span class="rank-value"
                ><b>{{ stats.shops ?? 0 }}</b> 家</span
              >
            </div>
            <div class="rank-row">
              <span class="rank-no">单</span>
              <span class="rank-name">今日订单</span>
              <span class="rank-value"
                ><b>{{ stats.today_orders ?? 0 }}</b> 笔</span
              >
            </div>
          </div>
        </div>
      </section>
    </div>

    <div class="dash-grid even">
      <section class="panel">
        <div class="panel-head">
          <h3>店铺成交排行</h3>
          <span class="right tip">按 GMV 降序</span>
        </div>
        <div class="panel-body">
          <div v-if="!ranking.length" class="empty-block">暂无成交数据</div>
          <div v-else class="rank-list">
            <div
              v-for="(item, index) in ranking"
              :key="item.name"
              class="rank-row"
              :class="`top${index + 1}`"
            >
              <span class="rank-no">{{ index + 1 }}</span>
              <span class="rank-name" :title="item.name">{{ item.name }}</span>
              <span class="rank-value"
                ><b>¥{{ compact(item.gmv) }}</b> · {{ item.orders }} 单</span
              >
              <span class="rank-bar"><i :style="{ width: `${(item.gmv / maxRankGmv) * 100}%` }" /></span>
            </div>
          </div>
        </div>
      </section>

      <section class="panel">
        <div class="panel-head">
          <h3>一级类目商品分布</h3>
          <span class="right tip">在售 SPU 数</span>
        </div>
        <div class="panel-body">
          <div v-if="!categories.length" class="empty-block">暂无类目数据</div>
          <div v-else class="rank-list">
            <div v-for="item in categories" :key="item.name" class="rank-row">
              <span class="rank-no">类</span>
              <span class="rank-name">{{ item.name }}</span>
              <span class="rank-value"
                ><b>{{ item.value }}</b> 个</span
              >
              <span class="rank-bar"><i :style="{ width: `${(item.value / maxCatValue) * 100}%` }" /></span>
            </div>
          </div>
        </div>
      </section>
    </div>

    <section class="panel" style="margin-top: 14px">
      <div class="panel-head">
        <h3>最新订单</h3>
        <RouterLink to="/console/orders" class="right tip">进入订单中心 ›</RouterLink>
      </div>
      <el-table :data="recent" size="small">
        <el-table-column label="订单号" width="200">
          <template #default="{ row }">
            <b>{{ row.order_no }}</b>
            <div class="muted">{{ row.created_at?.replace('T', ' ').slice(0, 16) }}</div>
          </template>
        </el-table-column>
        <el-table-column label="店铺" min-width="180">
          <template #default="{ row }">{{ row.shop_names?.join('、') || '—' }}</template>
        </el-table-column>
        <el-table-column label="商品" min-width="240">
          <template #default="{ row }">{{ row.items?.[0]?.title_snapshot || '—' }}</template>
        </el-table-column>
        <el-table-column label="金额" width="120" align="right">
          <template #default="{ row }">
            <span class="money">¥{{ money(row.total) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>
