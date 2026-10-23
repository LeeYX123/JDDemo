<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import PageHead from '../../components/PageHead.vue'
import { api } from '../../api'

const TABS = [
  { value: '', label: '全部' },
  { value: 'pending', label: '待处理' },
  { value: 'refunded', label: '已同意' },
  { value: 'rejected', label: '已驳回' },
]

const loading = ref(false)
const rows = ref([])
const status = ref('')
const total = ref(0)
const page = ref(1)

const visible = ref(false)
const submitting = ref(false)
const current = ref(null)
const form = reactive({ action: 'approve', reply: '已核实，同意本次售后申请' })

const money = (value) => Number(value || 0).toFixed(2)
const statusType = (value) =>
  ({ pending: 'warning', refunded: 'success', rejected: 'info', approved: 'primary' })[value] || 'info'

async function load() {
  loading.value = true
  try {
    const data = await api.get('/merchant/aftersales/', { status: status.value || undefined })
    rows.value = data || []
    total.value = rows.value.length
  } finally {
    loading.value = false
  }
}

function switchTab(value) {
  status.value = value
  page.value = 1
  load()
}

function open(row, action) {
  current.value = row
  form.action = action
  form.reply =
    action === 'approve'
      ? '已核实，同意本次售后申请，退款将于 1-3 个工作日原路退回'
      : '商品状态与描述一致，暂不支持该售后申请'
  visible.value = true
}

async function submit() {
  submitting.value = true
  try {
    await api.post('/merchant/aftersales/', {
      id: current.value.id,
      action: form.action,
      reply: form.reply,
    })
    ElMessage.success(form.action === 'approve' ? '已同意售后，库存已回滚' : '已驳回售后')
    visible.value = false
    load()
  } finally {
    submitting.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <PageHead title="售后管理" desc="同意退款会自动回滚库存并把订单置为已退款；驳回则订单回到已完成">
      <template #actions>
        <el-button @click="load">刷新</el-button>
      </template>
    </PageHead>

    <section class="panel">
      <div class="toolbar">
        <el-radio-group :model-value="status" @change="switchTab">
          <el-radio-button v-for="tab in TABS" :key="tab.value" :value="tab.value">
            {{ tab.label }}
          </el-radio-button>
        </el-radio-group>
        <span class="grow muted">共 {{ total }} 条售后记录</span>
      </div>

      <el-table v-loading="loading" :data="rows">
        <el-table-column label="售后单 / 订单号" width="190">
          <template #default="{ row }">
            <b>AS{{ String(row.id).padStart(6, '0') }}</b>
            <div class="muted">{{ row.order_no }}</div>
          </template>
        </el-table-column>
        <el-table-column label="商品" min-width="260">
          <template #default="{ row }">
            <div class="goods-cell">
              <span class="goods-thumb">{{ row.image_seed % 2 ? '📦' : '🎁' }}</span>
              <div class="goods-info">
                <b>{{ row.title }}</b>
                <span>{{ row.type_label }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="申请原因" min-width="180">
          <template #default="{ row }">
            <div>{{ row.reason }}</div>
            <div class="muted">{{ row.description }}</div>
          </template>
        </el-table-column>
        <el-table-column label="退款金额" width="110" align="right">
          <template #default="{ row }">
            <span class="money">¥{{ money(row.amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="96">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small" effect="light">{{ row.status_label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="申请时间" width="150">
          <template #default="{ row }">{{ row.created_at?.replace('T', ' ').slice(0, 16) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'pending'">
              <el-button link type="danger" size="small" @click="open(row, 'approve')">同意</el-button>
              <el-button link size="small" @click="open(row, 'reject')">驳回</el-button>
            </template>
            <span v-else class="muted">已处理</span>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="visible" :title="form.action === 'approve' ? '同意售后' : '驳回售后'" width="480px">
      <template v-if="current">
        <el-descriptions :column="1" border size="small" style="margin-bottom: 16px">
          <el-descriptions-item label="商品">{{ current.title }}</el-descriptions-item>
          <el-descriptions-item label="退款金额">¥{{ money(current.amount) }}</el-descriptions-item>
          <el-descriptions-item label="买家原因">{{ current.reason }}</el-descriptions-item>
        </el-descriptions>
        <el-form label-position="top">
          <el-form-item :label="form.action === 'approve' ? '处理说明' : '驳回原因'">
            <el-input v-model="form.reply" type="textarea" :rows="3" maxlength="120" show-word-limit />
          </el-form-item>
        </el-form>
        <el-alert
          v-if="form.action === 'approve'"
          type="warning"
          :closable="false"
          title="同意后库存将自动回滚，订单状态变为「已退款」且不可撤销。"
        />
      </template>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button
          :type="form.action === 'approve' ? 'danger' : 'primary'"
          :loading="submitting"
          @click="submit"
        >
          确认{{ form.action === 'approve' ? '同意' : '驳回' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>
