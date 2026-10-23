<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import PageHead from '../../components/PageHead.vue'
import StatCard from '../../components/StatCard.vue'
import { api } from '../../api'

const loading = ref(true)
const saving = ref(false)
const shop = ref({})
const form = reactive({ name: '', description: '', logo: '' })

async function load() {
  loading.value = true
  try {
    const data = await api.get('/merchant/shop/')
    shop.value = data || {}
    Object.assign(form, {
      name: data.name || '',
      description: data.description || '',
      logo: data.logo || '',
    })
  } finally {
    loading.value = false
  }
}

async function save() {
  if (!form.name.trim()) return ElMessage.warning('请填写店铺名称')
  saving.value = true
  try {
    const data = await api.patch('/merchant/shop/', { ...form })
    shop.value = data
    ElMessage.success('店铺信息已保存，前台将展示新名称')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div v-loading="loading">
    <PageHead title="店铺设置" desc="店铺名称与简介会同步展示在商品详情页与购物车" />

    <div class="stat-grid" style="grid-template-columns: repeat(3, minmax(0, 1fr))">
      <StatCard label="店铺评分" :value="shop.rating ?? '-'" hint="满分 5.0" />
      <StatCard label="商品数量" :value="shop.product_count ?? 0" hint="含在售与下架" />
      <StatCard label="累计订单" :value="shop.order_count ?? 0" hint="跨状态合计" />
    </div>

    <div class="dash-grid even">
      <section class="panel">
        <div class="panel-head"><h3>基础资料</h3></div>
        <div class="panel-body">
          <el-form label-position="top">
            <el-form-item label="店铺名称" required>
              <el-input v-model="form.name" maxlength="40" show-word-limit />
            </el-form-item>
            <el-form-item label="店铺简介">
              <el-input
                v-model="form.description"
                type="textarea"
                :rows="3"
                maxlength="120"
                show-word-limit
              />
            </el-form-item>
            <el-form-item label="Logo 标识（emoji 或单字）">
              <el-input v-model="form.logo" maxlength="4" placeholder="例：星" />
            </el-form-item>
            <el-button type="primary" :loading="saving" @click="save">保存设置</el-button>
          </el-form>
        </div>
      </section>

      <section class="panel">
        <div class="panel-head"><h3>店铺状态</h3></div>
        <div class="panel-body">
          <div class="goods-cell" style="margin-bottom: 18px">
            <span class="goods-thumb" style="width: 54px; height: 54px; font-size: 24px">
              {{ shop.logo || shop.name?.slice(0, 1) || '店' }}
            </span>
            <div class="goods-info">
              <b style="font-size: 16px">{{ shop.name || '未命名店铺' }}</b>
              <span>{{ shop.description || '暂无简介' }}</span>
            </div>
          </div>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="店铺 ID">{{ shop.id }}</el-descriptions-item>
            <el-descriptions-item label="入驻状态">
              <el-tag :type="shop.approved ? 'success' : 'warning'" size="small" effect="light">
                {{ shop.approved ? '已通过审核' : '待平台审核' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="经营状态">
              <el-tag :type="shop.enabled ? 'success' : 'info'" size="small" effect="light">
                {{ shop.enabled ? '正常营业' : '已被平台暂停' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="店铺负责人">{{ shop.owner_name || '—' }}</el-descriptions-item>
          </el-descriptions>
          <p class="muted" style="margin-top: 14px; font-size: 12px; line-height: 1.8">
            入驻状态与经营状态由平台管理端控制，商家端仅可维护店铺展示信息。
          </p>
        </div>
      </section>
    </div>
  </div>
</template>
