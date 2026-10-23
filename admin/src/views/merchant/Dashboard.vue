<script setup>
import { computed, onMounted, ref } from 'vue'

import PageHead from '../../components/PageHead.vue'
import StatCard from '../../components/StatCard.vue'
import TrendChart from '../../components/TrendChart.vue'
import { api } from '../../api'
import { statusLabel } from '../../menus'

const loading = ref(true)
const data = ref({})
const stats = computed(() => data.value.stats || {})
const trend = computed(() => data.value.trend || [])
const shop = computed(() => data.value.shop || {})
const recent = computed(() => data.value.recent_orders || [])
const topProducts = computed(() => data.value.top_products || [])
const maxSales = computed(() => Math.max(...topProducts.value.map((p) => p.sales), 1))

const money = (value) => Number(value || 0).toFixed(2)
const compact = (value) => {
  const n = Number(value || 0)
  if (n >= 10000) return `${(n / 10000).toFixed(1)}万`
  return n.toFixed(0)
}
const orderTitle = (order) => order.items?.[0]?.title_snapshot || '—'
const orderCount = (order) => (order.items || []).reduce((n, i) => n + i.quantity, 0)

async function load() {
  loading.value = true
  try {
    data.value = (await api.get('/merchant/dashboard/')) || {}
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div v-loading="loading">
    <PageHead title="数据看板" desc="今日经营概况与近 7 日走势，数据实时来自后端聚合">
      <template #actions>
        <el-button @click="load">刷新数据</el-button>
        <el-button type="primary" @click="$router.push('/merchant/products')">管理商品</el-button>
      </template>
    </PageHead>

    <div class="stat-grid">
      <StatCard label="今日订单" :value="stats.today_orders ?? 0" hint="实时统计" />
      <StatCard label="今日 GMV" unit="¥" :value="money(stats.today_gmv)" hint="含运费" />
      <StatCard
        label="待发货"
        :value="stats.pending_ship ?? 0"
        :hint="stats.pending_ship ? '需要尽快处理' : '暂无待办'"
        hint-type="warn"
      />
      <StatCard
        label="待售后"
        :value="stats.pending_aftersale ?? 0"
        :hint="stats.pending_aftersale ? '请及时审核' : '暂无待办'"
        hint-type="warn"
      />
      <StatCard label="在售商品" :value="stats.on_sale ?? 0" :hint="`共 ${stats.products ?? 0} 个 SPU`" />
    </div>

    <div class="dash-grid">
      <section class="panel">
        <div class="panel-head">
          <h3>近 7 日成交趋势</h3>
          <span class="tip">单位：元</span>
          <div class="right legend"><i style="background: #e1251b" />GMV</div>
        </div>
        <div class="panel-body">
          <TrendChart
            :data="trend"
            value-key="gmv"
            label-key="date"
            type="bar"
            color="#e1251b"
            :height="250"
            :formatter="compact"
          />
        </div>
      </section>

      <section class="panel">
        <div class="panel-head">
          <h3>店铺信息</h3>
          <span class="right tip">ID {{ shop.id }}</span>
        </div>
        <div class="panel-body">
          <div class="goods-cell" style="margin-bottom: 14px">
            <span class="goods-thumb" style="width: 46px; height: 46px; font-size: 20px">🏬</span>
            <div class="goods-info">
              <b style="font-size: 15px">{{ shop.name }}</b>
              <span>评分 {{ shop.rating }} · {{ shop.approved ? '已入驻' : '待审核' }}</span>
            </div>
          </div>
          <p class="muted" style="font-size: 12.5px; line-height: 1.8; margin: 0 0 14px">
            {{ shop.description || '店铺暂未填写简介' }}
          </p>
          <div class="rank-list">
            <div class="rank-row">
              <span class="rank-no">订</span>
              <span class="rank-name">累计订单</span>
              <span class="rank-value"
                ><b>{{ stats.orders ?? 0 }}</b> 笔</span
              >
            </div>
            <div class="rank-row">
              <span class="rank-no">销</span>
              <span class="rank-name">累计成交额</span>
              <span class="rank-value"
                ><b>¥{{ money(stats.gmv) }}</b></span
              >
            </div>
            <div class="rank-row">
              <span class="rank-no">货</span>
              <span class="rank-name">商品总数</span>
              <span class="rank-value"
                ><b>{{ stats.products ?? 0 }}</b> 个</span
              >
            </div>
          </div>
        </div>
      </section>
    </div>

    <div class="dash-grid even">
      <section class="panel">
        <div class="panel-head">
          <h3>热销商品 Top 5</h3>
          <span class="right tip">按销量排序</span>
        </div>
        <div class="panel-body">
          <div v-if="!topProducts.length" class="empty-block">暂无成交数据</div>
          <div v-else class="rank-list">
            <div
              v-for="(item, index) in topProducts"
              :key="item.title_snapshot"
              class="rank-row"
              :class="`top${index + 1}`"
              style="grid-template-columns: 20px 1fr auto"
            >
              <span class="rank-no">{{ index + 1 }}</span>
              <span class="rank-name" :title="item.title_snapshot">{{ item.title_snapshot }}</span>
              <span class="rank-value"
                ><b>{{ item.sales }}</b> 件</span
              >
              <span class="rank-bar" style="grid-column: 2 / 3">
                <i :style="{ width: `${(item.sales / maxSales) * 100}%` }" />
              </span>
            </div>
          </div>
        </div>
      </section>

      <section class="panel">
        <div class="panel-head">
          <h3>最近订单</h3>
          <RouterLink to="/merchant/orders" class="right tip">查看全部 ›</RouterLink>
        </div>
        <el-table :data="recent" size="small" :show-header="true">
          <el-table-column label="订单 / 商品" min-width="240">
            <template #default="{ row }">
              <div class="goods-cell">
                <span class="goods-thumb">{{ row.items?.[0]?.image_seed % 2 ? '📦' : '🎁' }}</span>
                <div class="goods-info">
                  <b>{{ orderTitle(row) }}</b>
                  <span>{{ row.order_no }} · {{ orderCount(row) }} 件</span>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="金额" width="110" align="right">
            <template #default="{ row }">
              <span class="money">¥{{ money(row.total) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="96">
            <template #default="{ row }">
              <el-tag size="small" effect="plain">{{ statusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </section>
    </div>
  </div>
</template>
