<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import PageHead from '../../components/PageHead.vue'
import { api } from '../../api'
import { ORDER_STATUS, statusLabel } from '../../menus'

const activeTab = ref('orders')
const loading = ref(false)
const rows = ref([])
const total = ref(0)
const shops = ref([])
const query = reactive({ page: 1, size: 10, status: '', q: '', shop: '' })

const drawerVisible = ref(false)
const current = ref(null)

const sales = ref([])
const salesLoading = ref(false)
const salesStatus = ref('pending')

const money = (value) => Number(value || 0).toFixed(2)
const itemCount = (order) => (order.items || []).reduce((n, i) => n + i.quantity, 0)
const statusType = (status) =>
  ({
    pending_pay: 'warning',
    paid: 'danger',
    shipped: 'primary',
    completed: 'success',
    cancelled: 'info',
    aftersale: 'warning',
    refunded: 'info',
  })[status] || 'info'

async function load() {
  loading.value = true
  try {
    const data = await api.get('/console/orders/', {
      page: query.page,
      size: query.size,
      status: query.status || undefined,
      q: query.q || undefined,
      shop: query.shop || undefined,
    })
    rows.value = data.results || []
    total.value = data.total || 0
  } finally {
    loading.value = false
  }
}

async function loadShops() {
  shops.value = (await api.get('/console/shops/')) || []
}

async function loadSales() {
  salesLoading.value = true
  try {
    sales.value = (await api.get('/console/aftersales/', { status: salesStatus.value || undefined })) || []
  } finally {
    salesLoading.value = false
  }
}

function search() {
  query.page = 1
  load()
}

function openDetail(row) {
  current.value = row
  drawerVisible.value = true
}

async function handleSale(row, action) {
  const text =
    action === 'approve'
      ? `确认同意「${row.title}」的售后并退款 ¥${money(row.amount)}？`
      : '确认驳回该售后申请？'
  try {
    await ElMessageBox.confirm(text, '售后处理', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  await api.post('/console/aftersales/', {
    id: row.id,
    action,
    reply: action === 'approve' ? '平台已介入并同意退款' : '平台复核后认为不符合售后条件',
  })
  ElMessage.success('处理完成')
  loadSales()
  load()
}

function switchTab(name) {
  activeTab.value = name
  if (name === 'aftersales') loadSales()
}

onMounted(() => {
  load()
  loadShops()
  loadSales()
})
</script>

<template>
  <div>
    <PageHead title="订单中心" desc="跨店查询全站订单，并可处理平台层售后工单">
      <template #actions>
        <el-button @click="activeTab === 'orders' ? load() : loadSales()">刷新</el-button>
      </template>
    </PageHead>

    <el-tabs v-model="activeTab" @tab-change="switchTab">
      <el-tab-pane label="订单列表" name="orders">
        <section class="panel">
          <div class="toolbar">
            <el-select
              v-model="query.status"
              placeholder="全部状态"
              clearable
              style="width: 140px"
              @change="search"
            >
              <el-option
                v-for="item in ORDER_STATUS"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
            <el-select
              v-model="query.shop"
              placeholder="全部店铺"
              clearable
              filterable
              style="width: 190px"
              @change="search"
            >
              <el-option v-for="shop in shops" :key="shop.id" :label="shop.name" :value="shop.id" />
            </el-select>
            <el-input
              v-model="query.q"
              placeholder="订单号 / 商品标题"
              clearable
              style="max-width: 220px"
              @keyup.enter="search"
              @clear="search"
            />
            <el-button type="primary" plain @click="search">查询</el-button>
            <span class="grow muted">共 {{ total }} 笔订单</span>
          </div>

          <el-table v-loading="loading" :data="rows">
            <el-table-column label="订单号 / 时间" min-width="190">
              <template #default="{ row }">
                <b>{{ row.order_no }}</b>
                <div class="muted">{{ row.created_at?.replace('T', ' ').slice(0, 16) }}</div>
              </template>
            </el-table-column>
            <el-table-column label="店铺" min-width="150">
              <template #default="{ row }">{{ row.shop_names?.join('、') || '—' }}</template>
            </el-table-column>
            <el-table-column label="商品" min-width="260">
              <template #default="{ row }">
                <div class="goods-cell">
                  <span class="goods-thumb">{{ row.items?.[0]?.image_seed % 2 ? '📦' : '🎁' }}</span>
                  <div class="goods-info">
                    <b>{{ row.items?.[0]?.title_snapshot || '—' }}</b>
                    <span>共 {{ itemCount(row) }} 件</span>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="买家" width="100">
              <template #default="{ row }">{{ row.address_snapshot?.receiver || '—' }}</template>
            </el-table-column>
            <el-table-column label="金额" width="120" align="right">
              <template #default="{ row }">
                <span class="money">¥{{ money(row.total) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="statusType(row.status)" size="small" effect="light">
                  {{ statusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="90" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="openDetail(row)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-model:current-page="query.page"
            :page-size="query.size"
            :total="total"
            layout="total, prev, pager, next"
            background
            @current-change="load"
          />
        </section>
      </el-tab-pane>

      <el-tab-pane label="售后工单" name="aftersales">
        <section class="panel">
          <div class="toolbar">
            <el-radio-group v-model="salesStatus" @change="loadSales">
              <el-radio-button value="pending">待处理</el-radio-button>
              <el-radio-button value="refunded">已退款</el-radio-button>
              <el-radio-button value="rejected">已驳回</el-radio-button>
              <el-radio-button value="">全部</el-radio-button>
            </el-radio-group>
            <span class="grow muted">共 {{ sales.length }} 条</span>
          </div>

          <el-table v-loading="salesLoading" :data="sales">
            <el-table-column label="售后单 / 订单" width="190">
              <template #default="{ row }">
                <b>AS{{ String(row.id).padStart(6, '0') }}</b>
                <div class="muted">{{ row.order_no }}</div>
              </template>
            </el-table-column>
            <el-table-column label="店铺" prop="shop_name" width="150" />
            <el-table-column label="商品" min-width="240">
              <template #default="{ row }">
                <div class="goods-cell">
                  <span class="goods-thumb">{{ row.image_seed % 2 ? '📦' : '🎁' }}</span>
                  <div class="goods-info">
                    <b>{{ row.title }}</b>
                    <span>{{ row.type_label }} · {{ row.reason }}</span>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="金额" width="110" align="right">
              <template #default="{ row }">
                <span class="money">¥{{ money(row.amount) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="96">
              <template #default="{ row }">
                <el-tag
                  size="small"
                  effect="light"
                  :type="
                    row.status === 'refunded' ? 'success' : row.status === 'pending' ? 'warning' : 'info'
                  "
                >
                  {{ row.status_label }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <template v-if="row.status === 'pending'">
                  <el-button link type="danger" size="small" @click="handleSale(row, 'approve')">
                    同意退款
                  </el-button>
                  <el-button link size="small" @click="handleSale(row, 'reject')">驳回</el-button>
                </template>
                <span v-else class="muted">{{ row.reply || '已处理' }}</span>
              </template>
            </el-table-column>
          </el-table>
        </section>
      </el-tab-pane>
    </el-tabs>

    <el-drawer v-model="drawerVisible" title="订单详情（平台视角）" size="480px">
      <template v-if="current">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="订单号">{{ current.order_no }}</el-descriptions-item>
          <el-descriptions-item label="批次号">{{ current.batch_no || '—' }}</el-descriptions-item>
          <el-descriptions-item label="店铺">{{ current.shop_names?.join('、') }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ statusLabel(current.status) }}</el-descriptions-item>
          <el-descriptions-item label="收货信息">
            {{ current.address_snapshot?.receiver }} · {{ current.address_snapshot?.phone }}<br />
            {{ current.address_snapshot?.full_text }}
          </el-descriptions-item>
          <el-descriptions-item label="物流">
            {{ current.tracking_no ? `${current.tracking_company} ${current.tracking_no}` : '未发货' }}
          </el-descriptions-item>
        </el-descriptions>

        <h4 style="margin: 20px 0 10px; font-size: 13px">商品清单</h4>
        <div
          v-for="item in current.items"
          :key="item.id"
          class="goods-cell"
          style="padding: 10px 0; border-bottom: 1px solid var(--line)"
        >
          <span class="goods-thumb">{{ item.image_seed % 2 ? '📦' : '🎁' }}</span>
          <div class="goods-info">
            <b>{{ item.title_snapshot }}</b>
            <span>{{ item.shop_name }} · × {{ item.quantity }}</span>
          </div>
          <span class="money" style="margin-left: auto">¥{{ money(item.price_snapshot) }}</span>
        </div>

        <div style="margin-top: 16px; display: grid; gap: 8px; font-size: 12.5px">
          <div style="display: flex; justify-content: space-between">
            <span class="muted">商品金额</span><span>¥{{ money(current.subtotal) }}</span>
          </div>
          <div style="display: flex; justify-content: space-between">
            <span class="muted">运费</span><span>¥{{ money(current.freight) }}</span>
          </div>
          <div style="display: flex; justify-content: space-between; font-weight: 700">
            <span>订单总额</span><span class="money big">¥{{ money(current.total) }}</span>
          </div>
        </div>
      </template>
    </el-drawer>
  </div>
</template>
