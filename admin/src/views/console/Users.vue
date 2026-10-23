<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import PageHead from '../../components/PageHead.vue'
import { api } from '../../api'

const loading = ref(false)
const rows = ref([])
const total = ref(0)
const query = reactive({ page: 1, size: 10, role: '', q: '' })

const ROLE_TAG = {
  buyer: { label: '买家', type: 'info' },
  merchant: { label: '商家', type: 'warning' },
  console: { label: '平台', type: 'danger' },
}
const activeCount = computed(() => rows.value.filter((row) => row.is_active).length)

async function load() {
  loading.value = true
  try {
    const data = await api.get('/console/users/', {
      page: query.page,
      size: query.size,
      role: query.role || undefined,
      q: query.q || undefined,
    })
    rows.value = data.results || []
    total.value = data.total || 0
  } finally {
    loading.value = false
  }
}

function search() {
  query.page = 1
  load()
}

async function toggle(row) {
  const data = await api.post(`/console/users/${row.id}/toggle/`)
  row.is_active = data.is_active
  ElMessage.success(data.is_active ? '账号已启用' : '账号已禁用')
}

onMounted(load)
</script>

<template>
  <div>
    <PageHead title="用户管理" desc="买家、商家、平台共用一套账号体系；禁用后该账号无法登录">
      <template #actions>
        <el-button @click="load">刷新</el-button>
      </template>
    </PageHead>

    <section class="panel">
      <div class="toolbar">
        <el-select
          v-model="query.role"
          placeholder="全部角色"
          clearable
          style="width: 140px"
          @change="search"
        >
          <el-option label="买家" value="buyer" />
          <el-option label="商家" value="merchant" />
          <el-option label="平台" value="console" />
        </el-select>
        <el-input
          v-model="query.q"
          placeholder="搜索手机号"
          clearable
          style="max-width: 200px"
          @keyup.enter="search"
          @clear="search"
        />
        <el-button type="primary" plain @click="search">查询</el-button>
        <span class="grow muted">共 {{ total }} 个账号 · 本页启用 {{ activeCount }} 个</span>
      </div>

      <el-table v-loading="loading" :data="rows">
        <el-table-column label="用户" min-width="240">
          <template #default="{ row }">
            <div class="goods-cell">
              <span class="goods-thumb" style="border-radius: 50%">{{
                (row.nickname || row.username).slice(-2)
              }}</span>
              <div class="goods-info">
                <b>{{ row.nickname || row.username }}</b>
                <span>{{ row.username }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="ROLE_TAG[row.role]?.type || 'info'" size="small" effect="light">
              {{ ROLE_TAG[row.role]?.label || row.role }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="邮箱" min-width="180">
          <template #default="{ row }">{{ row.email || '—' }}</template>
        </el-table-column>
        <el-table-column label="注册时间" width="150" prop="date_joined" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small" effect="plain">
              {{ row.is_active ? '正常' : '已禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-tooltip v-if="row.role === 'console'" content="平台账号不可禁用" placement="top">
              <span class="muted">受保护</span>
            </el-tooltip>
            <el-button
              v-else
              link
              :type="row.is_active ? 'danger' : 'success'"
              size="small"
              @click="toggle(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
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
  </div>
</template>
