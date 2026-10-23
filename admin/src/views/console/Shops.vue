<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import PageHead from '../../components/PageHead.vue'
import { api } from '../../api'

const loading = ref(false)
const rows = ref([])
const filter = ref('')
const keyword = ref('')

const pendingCount = computed(() => rows.value.filter((row) => !row.approved).length)

async function load() {
  loading.value = true
  try {
    const data = await api.get('/console/shops/', {
      approved: filter.value === '' ? undefined : filter.value,
      q: keyword.value || undefined,
    })
    rows.value = data || []
  } finally {
    loading.value = false
  }
}

function switchFilter(value) {
  filter.value = value
  load()
}

async function audit(row, action, confirmText) {
  try {
    await ElMessageBox.confirm(confirmText, '操作确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  await api.post(`/console/shops/${row.id}/audit/`, { action })
  ElMessage.success('操作成功')
  load()
}

onMounted(load)
</script>

<template>
  <div>
    <PageHead title="商家审核" desc="审核通过后店铺商品方可上架；停用后该店铺商品对买家不可见">
      <template #actions>
        <el-button @click="load">刷新</el-button>
      </template>
    </PageHead>

    <section class="panel">
      <div class="toolbar">
        <el-radio-group :model-value="filter" @change="switchFilter">
          <el-radio-button value="">全部店铺</el-radio-button>
          <el-radio-button value="false">待审核</el-radio-button>
          <el-radio-button value="true">已通过</el-radio-button>
        </el-radio-group>
        <el-input
          v-model="keyword"
          placeholder="搜索店铺名称"
          clearable
          style="max-width: 220px"
          @keyup.enter="load"
          @clear="load"
        />
        <el-button type="primary" plain @click="load">查询</el-button>
        <span class="grow muted">待审核 {{ pendingCount }} 家 · 共 {{ rows.length }} 家</span>
      </div>

      <el-table v-loading="loading" :data="rows">
        <el-table-column label="店铺" min-width="260">
          <template #default="{ row }">
            <div class="goods-cell">
              <span class="goods-thumb">{{ row.logo || row.name.slice(0, 1) }}</span>
              <div class="goods-info">
                <b>{{ row.name }}</b>
                <span>ID {{ row.id }} · 评分 {{ row.rating }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="负责人" width="130">
          <template #default="{ row }">{{ row.owner_name || '—' }}</template>
        </el-table-column>
        <el-table-column label="商品数" prop="product_count" width="90" align="right" />
        <el-table-column label="简介" min-width="200">
          <template #default="{ row }">
            <span class="muted">{{ row.description || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="130">
          <template #default="{ row }">
            <el-tag v-if="!row.approved" type="warning" size="small" effect="light">待审核</el-tag>
            <el-tag v-else-if="!row.enabled" type="info" size="small" effect="light">已停用</el-tag>
            <el-tag v-else type="success" size="small" effect="light">正常营业</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <template v-if="!row.approved">
              <el-button
                link
                type="primary"
                size="small"
                @click="audit(row, 'approve', `确认通过「${row.name}」的入驻审核？`)"
              >
                通过
              </el-button>
              <el-button
                link
                type="danger"
                size="small"
                @click="audit(row, 'reject', `确认驳回「${row.name}」的入驻申请？`)"
              >
                驳回
              </el-button>
            </template>
            <template v-else>
              <el-button
                v-if="row.enabled"
                link
                type="warning"
                size="small"
                @click="audit(row, 'disable', `停用后「${row.name}」的商品将对买家不可见，确认继续？`)"
              >
                停用店铺
              </el-button>
              <el-button
                v-else
                link
                type="success"
                size="small"
                @click="audit(row, 'enable', `确认恢复「${row.name}」的经营？`)"
              >
                恢复经营
              </el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>
