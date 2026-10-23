<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import PageHead from '../../components/PageHead.vue'
import { api } from '../../api'
import { PRODUCT_STATUS, productStatus } from '../../menus'

const route = useRoute()
const loading = ref(false)
const rows = ref([])
const total = ref(0)
const shops = ref([])
const query = reactive({ page: 1, size: 10, q: '', status: '', shop: '' })

const rejectVisible = ref(false)
const rejecting = ref(false)
const current = ref(null)
const reason = ref('商品标题与实物不符，请修改后重新提交')

const money = (value) => Number(value || 0).toFixed(2)

async function load() {
  loading.value = true
  try {
    const data = await api.get('/console/products/', {
      page: query.page,
      size: query.size,
      q: query.q || undefined,
      status: query.status || undefined,
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

function search() {
  query.page = 1
  load()
}

async function audit(row, action, message) {
  if (message) {
    try {
      await ElMessageBox.confirm(message, '操作确认', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      })
    } catch {
      return
    }
  }
  await api.post(`/console/products/${row.id}/audit/`, { action })
  ElMessage.success('操作成功')
  load()
}

function openReject(row) {
  current.value = row
  reason.value = '商品标题与实物不符，请修改后重新提交'
  rejectVisible.value = true
}

async function submitReject() {
  if (!reason.value.trim()) return ElMessage.warning('请填写驳回原因')
  rejecting.value = true
  try {
    await api.post(`/console/products/${current.value.id}/audit/`, {
      action: 'reject',
      reason: reason.value.trim(),
    })
    ElMessage.success('已驳回，商家可在后台修改后重新提交')
    rejectVisible.value = false
    load()
  } finally {
    rejecting.value = false
  }
}

onMounted(() => {
  const status = typeof route.query.status === 'string' ? route.query.status : ''
  query.status = status
  load()
  loadShops()
})
</script>

<template>
  <div>
    <PageHead title="商品审核" desc="商家提交的新品需审核通过才上架；强制下架会立即从前台消失">
      <template #actions>
        <el-button @click="load">刷新</el-button>
      </template>
    </PageHead>

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
            v-for="item in PRODUCT_STATUS"
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
          placeholder="搜索商品标题"
          clearable
          style="max-width: 220px"
          @keyup.enter="search"
          @clear="search"
        />
        <el-button type="primary" plain @click="search">查询</el-button>
        <span class="grow muted">共 {{ total }} 个商品</span>
      </div>

      <el-table v-loading="loading" :data="rows">
        <el-table-column label="商品" min-width="320">
          <template #default="{ row }">
            <div class="goods-cell">
              <span class="goods-thumb">{{
                ['📱', '🎧', '👟', '💄', '🧸', '🍎', '🧊', '🍳'][row.image_seed % 8]
              }}</span>
              <div class="goods-info">
                <b>{{ row.title }}</b>
                <span>{{ row.category_name }} · {{ row.brand_name }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="店铺" prop="shop_name" width="150" />
        <el-table-column label="价格" width="120" align="right">
          <template #default="{ row }">
            <span class="money">¥{{ money(row.price) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="库存" prop="stock" width="80" align="right" />
        <el-table-column label="销量" prop="sales" width="80" align="right" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="productStatus(row.status).type" size="small" effect="light">
              {{ productStatus(row.status).label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="190" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'pending'">
              <el-button
                link
                type="primary"
                size="small"
                @click="audit(row, 'approve', `确认通过「${row.title}」的审核？`)"
              >
                通过
              </el-button>
              <el-button link type="danger" size="small" @click="openReject(row)">驳回</el-button>
            </template>
            <template v-else-if="row.status === 'on'">
              <el-button
                link
                type="warning"
                size="small"
                @click="audit(row, 'off', `强制下架「${row.title}」后前台立即不可见，确认继续？`)"
              >
                强制下架
              </el-button>
            </template>
            <template v-else>
              <el-button link type="success" size="small" @click="audit(row, 'on')">恢复上架</el-button>
            </template>
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

    <el-dialog v-model="rejectVisible" title="驳回商品" width="460px">
      <el-form label-position="top">
        <el-form-item label="商品">
          <el-input :model-value="current?.title" disabled />
        </el-form-item>
        <el-form-item label="驳回原因（商家可见）" required>
          <el-input v-model="reason" type="textarea" :rows="3" maxlength="120" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectVisible = false">取消</el-button>
        <el-button type="danger" :loading="rejecting" @click="submitReject">确认驳回</el-button>
      </template>
    </el-dialog>
  </div>
</template>
