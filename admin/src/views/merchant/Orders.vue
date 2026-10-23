<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import PageHead from '../../components/PageHead.vue'
import { api } from '../../api'
import { ORDER_STATUS, statusLabel } from '../../menus'

const TABS = [{ value: '', label: '全部' }, ...ORDER_STATUS]

const loading = ref(false)
const rows = ref([])
const total = ref(0)
const query = reactive({ page: 1, size: 10, status: '', q: '' })

const shipVisible = ref(false)
const shipping = ref(false)
const shipForm = reactive({ order_no: '', tracking_company: '京东物流', tracking_no: '' })

const drawerVisible = ref(false)
const current = ref(null)

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

const receiver = computed(() => current.value?.address_snapshot?.receiver || '—')

async function load() {
  loading.value = true
  try {
    const data = await api.get('/merchant/orders/', {
      page: query.page,
      size: query.size,
      status: query.status || undefined,
      q: query.q || undefined,
    })
    rows.value = data.results || []
    total.value = data.total || 0
  } finally {
    loading.value = false
  }
}

function switchTab(value) {
  query.status = value
  query.page = 1
  load()
}

function search() {
  query.page = 1
  load()
}

function openShip(row) {
  shipForm.order_no = row.order_no
  shipForm.tracking_company = '京东物流'
  shipForm.tracking_no = `JDV${Date.now().toString().slice(-10)}`
  shipVisible.value = true
}

async function submitShip() {
  if (shipForm.tracking_no.trim().length < 6) return ElMessage.warning('请填写至少 6 位运单号')
  shipping.value = true
  try {
    await api.post(`/merchant/orders/${shipForm.order_no}/ship/`, {
      tracking_no: shipForm.tracking_no.trim(),
      tracking_company: shipForm.tracking_company,
    })
    ElMessage.success('发货成功')
    shipVisible.value = false
    load()
  } finally {
    shipping.value = false
  }
}

function shipFromDrawer() {
  const row = current.value
  drawerVisible.value = false
  if (row) openShip(row)
}

function openDetail(row) {
  current.value = row
  drawerVisible.value = true
}

onMounted(load)
</script>

<template>
  <div>
    <PageHead title="订单管理" desc="仅展示本店订单，待发货订单请及时填写运单号">
      <template #actions>
        <el-button @click="load">刷新</el-button>
      </template>
    </PageHead>

    <section class="panel">
      <div class="toolbar">
        <el-radio-group :model-value="query.status" @change="switchTab">
          <el-radio-button v-for="tab in TABS" :key="tab.value" :value="tab.value">
            {{ tab.label }}
          </el-radio-button>
        </el-radio-group>
        <el-input
          v-model="query.q"
          class="grow"
          placeholder="订单号 / 商品标题"
          clearable
          style="max-width: 240px"
          @keyup.enter="search"
          @clear="search"
        />
      </div>

      <el-table v-loading="loading" :data="rows">
        <el-table-column label="订单号 / 下单时间" min-width="190">
          <template #default="{ row }">
            <b style="font-size: 12.5px">{{ row.order_no }}</b>
            <div class="muted">{{ row.created_at?.replace('T', ' ').slice(0, 19) }}</div>
          </template>
        </el-table-column>
        <el-table-column label="商品" min-width="280">
          <template #default="{ row }">
            <div class="goods-cell">
              <span class="goods-thumb">{{ row.items?.[0]?.image_seed % 2 ? '📦' : '🎁' }}</span>
              <div class="goods-info">
                <b>{{ row.items?.[0]?.title_snapshot || '—' }}</b>
                <span>共 {{ itemCount(row) }} 件 · {{ row.shop_names?.join('、') }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="收货人" width="110">
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
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openDetail(row)">详情</el-button>
            <el-button v-if="row.status === 'paid'" link type="danger" size="small" @click="openShip(row)">
              发货
            </el-button>
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

    <el-dialog v-model="shipVisible" title="订单发货" width="460px">
      <el-form label-position="top">
        <el-form-item label="订单号">
          <el-input :model-value="shipForm.order_no" disabled />
        </el-form-item>
        <el-form-item label="物流公司">
          <el-select v-model="shipForm.tracking_company" style="width: 100%">
            <el-option label="京东物流" value="京东物流" />
            <el-option label="顺丰速运" value="顺丰速运" />
            <el-option label="中通快递" value="中通快递" />
            <el-option label="圆通速递" value="圆通速递" />
          </el-select>
        </el-form-item>
        <el-form-item label="运单号" required>
          <el-input v-model="shipForm.tracking_no" maxlength="40" placeholder="请输入运单号" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="shipVisible = false">取消</el-button>
        <el-button type="primary" :loading="shipping" @click="submitShip">确认发货</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="drawerVisible" title="订单详情" size="480px">
      <template v-if="current">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="订单号">{{ current.order_no }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ statusLabel(current.status) }}</el-descriptions-item>
          <el-descriptions-item label="收货人">
            {{ receiver }} · {{ current.address_snapshot?.phone || '' }}
          </el-descriptions-item>
          <el-descriptions-item label="收货地址">
            {{ current.address_snapshot?.full_text || '—' }}
          </el-descriptions-item>
          <el-descriptions-item label="下单时间">
            {{ current.created_at?.replace('T', ' ').slice(0, 19) }}
          </el-descriptions-item>
          <el-descriptions-item v-if="current.tracking_no" label="物流">
            {{ current.tracking_company }} {{ current.tracking_no }}
          </el-descriptions-item>
          <el-descriptions-item v-if="current.remark" label="买家备注">
            {{ current.remark }}
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
            <span>{{ item.specs_snapshot?.['规格'] || '标准版' }} × {{ item.quantity }}</span>
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
            <span>实付金额</span><span class="money big">¥{{ money(current.total) }}</span>
          </div>
        </div>

        <el-button
          v-if="current.status === 'paid'"
          type="primary"
          style="width: 100%; margin-top: 20px"
          @click="shipFromDrawer"
        >
          立即发货
        </el-button>
      </template>
    </el-drawer>
  </div>
</template>
