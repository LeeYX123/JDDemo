<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import PageHead from '../../components/PageHead.vue'
import { api } from '../../api'
import { PRODUCT_STATUS, productStatus } from '../../menus'

const loading = ref(false)
const rows = ref([])
const total = ref(0)
const query = reactive({ page: 1, size: 10, q: '', status: '' })

const brands = ref([])
const categoryOptions = ref([])
const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref(null)

const emptyForm = () => ({
  title: '',
  subtitle: '',
  category_id: null,
  brand_id: null,
  price: '',
  market_price: '',
  stock: 100,
  spec: '标准版',
  tags: '新品|自营',
  image_seed: 1,
  status: 'pending',
})
const form = reactive(emptyForm())

const dialogTitle = computed(() => (editingId.value ? '编辑商品' : '新增商品'))
const money = (value) => Number(value || 0).toFixed(2)

function flattenCategories(nodes, out = []) {
  nodes.forEach((node) => {
    if (node.level === 3) out.push({ id: node.id, label: `${node.name}` })
    if (node.children?.length) flattenCategories(node.children, out)
  })
  return out
}

async function load() {
  loading.value = true
  try {
    const data = await api.get('/merchant/products/', {
      page: query.page,
      size: query.size,
      q: query.q || undefined,
      status: query.status || undefined,
    })
    rows.value = data.results || []
    total.value = data.total || 0
  } finally {
    loading.value = false
  }
}

async function loadOptions() {
  const [brandList, tree] = await Promise.all([api.get('/brands/'), api.get('/categories/')])
  brands.value = brandList || []
  categoryOptions.value = flattenCategories(tree || [])
}

function search() {
  query.page = 1
  load()
}

function resetQuery() {
  query.q = ''
  query.status = ''
  query.page = 1
  load()
}

function openCreate() {
  editingId.value = null
  Object.assign(form, emptyForm())
  if (!categoryOptions.value.length) loadOptions()
  dialogVisible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  Object.assign(form, {
    title: row.title,
    subtitle: row.subtitle || '',
    category_id: row.category_id,
    brand_id: row.brand_id,
    price: row.price,
    market_price: row.market_price,
    stock: row.stock,
    spec: '标准版',
    tags: row.tags || '新品|自营',
    image_seed: row.image_seed || 1,
    status: row.status,
  })
  if (!categoryOptions.value.length) loadOptions()
  dialogVisible.value = true
}

async function save() {
  if (!form.title.trim()) return ElMessage.warning('请填写商品标题')
  if (!form.category_id) return ElMessage.warning('请选择三级类目')
  if (!form.brand_id) return ElMessage.warning('请选择品牌')
  if (!Number(form.price)) return ElMessage.warning('请填写有效售价')

  saving.value = true
  try {
    if (editingId.value) {
      await api.patch(`/merchant/products/${editingId.value}/`, { ...form })
      ElMessage.success('商品已保存')
    } else {
      await api.post('/merchant/products/', { ...form })
      ElMessage.success('商品已提交，等待平台审核')
    }
    dialogVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function toggle(row) {
  const action = row.status === 'on' ? '下架' : '上架'
  try {
    await ElMessageBox.confirm(`确定要${action}「${row.title}」吗？`, `${action}商品`, {
      confirmButtonText: `确定${action}`,
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  const data = await api.post(`/merchant/products/${row.id}/toggle/`)
  row.status = data.status
  ElMessage.success(data.status === 'on' ? '已上架' : '已下架')
}

onMounted(() => {
  load()
  loadOptions()
})
</script>

<template>
  <div>
    <PageHead title="商品管理" desc="维护本店商品的价格、库存与上下架状态">
      <template #actions>
        <el-button type="primary" @click="openCreate">新增商品</el-button>
      </template>
    </PageHead>

    <section class="panel">
      <div class="toolbar">
        <el-input
          v-model="query.q"
          placeholder="搜索商品标题"
          clearable
          @keyup.enter="search"
          @clear="search"
        />
        <el-select v-model="query.status" placeholder="全部状态" clearable @change="search">
          <el-option
            v-for="item in PRODUCT_STATUS"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
        <el-button type="primary" plain @click="search">查询</el-button>
        <el-button @click="resetQuery">重置</el-button>
        <span class="grow muted">共 {{ total }} 个商品</span>
      </div>

      <el-table v-loading="loading" :data="rows" size="default">
        <el-table-column label="商品" min-width="320">
          <template #default="{ row }">
            <div class="goods-cell">
              <span class="goods-thumb">{{
                ['📱', '🎧', '👟', '💄', '🧸', '🍎', '🧊', '🍳'][row.image_seed % 8]
              }}</span>
              <div class="goods-info">
                <b>{{ row.title }}</b>
                <span>{{ row.category_name }} · {{ row.shop_name }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="品牌" prop="brand_name" width="110" />
        <el-table-column label="售价 / 划线价" width="150" align="right">
          <template #default="{ row }">
            <span class="money">¥{{ money(row.price) }}</span>
            <div class="muted" style="text-decoration: line-through">¥{{ money(row.market_price) }}</div>
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
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
            <el-button
              link
              :type="row.status === 'on' ? 'warning' : 'success'"
              size="small"
              @click="toggle(row)"
            >
              {{ row.status === 'on' ? '下架' : '上架' }}
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="620px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item label="商品标题" required>
          <el-input
            v-model="form.title"
            maxlength="120"
            placeholder="例：星野 旗舰 5G 智能手机 12GB+256GB 曜石黑"
          />
        </el-form-item>
        <el-form-item label="副标题">
          <el-input v-model="form.subtitle" maxlength="120" placeholder="一句话卖点" />
        </el-form-item>
        <div class="form-grid">
          <el-form-item label="三级类目" required>
            <el-select v-model="form.category_id" filterable placeholder="选择类目" style="width: 100%">
              <el-option
                v-for="item in categoryOptions"
                :key="item.id"
                :label="item.label"
                :value="item.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="品牌" required>
            <el-select v-model="form.brand_id" filterable placeholder="选择品牌" style="width: 100%">
              <el-option v-for="brand in brands" :key="brand.id" :label="brand.name" :value="brand.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="售价（元）" required>
            <el-input-number v-model="form.price" :min="0.01" :precision="2" :step="10" style="width: 100%" />
          </el-form-item>
          <el-form-item label="划线价（元）">
            <el-input-number
              v-model="form.market_price"
              :min="0"
              :precision="2"
              :step="10"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="库存">
            <el-input-number v-model="form.stock" :min="0" :max="999999" style="width: 100%" />
          </el-form-item>
          <el-form-item label="规格名">
            <el-input v-model="form.spec" maxlength="40" placeholder="例：12GB+256GB 曜石黑" />
          </el-form-item>
          <el-form-item label="商品标签（竖线分隔）" class="span2">
            <el-input v-model="form.tags" maxlength="80" placeholder="新品|自营|包邮" />
          </el-form-item>
          <el-form-item label="占位图配色">
            <el-select v-model="form.image_seed" style="width: 100%">
              <el-option v-for="n in 8" :key="n" :label="`配色 ${n}`" :value="n" />
            </el-select>
          </el-form-item>
          <el-form-item label="上架状态">
            <el-select v-model="form.status" style="width: 100%">
              <el-option label="保存草稿" value="draft" />
              <el-option label="提交审核" value="pending" />
              <el-option v-if="editingId" label="直接上架（已审核）" value="on" />
              <el-option v-if="editingId" label="下架" value="off" />
            </el-select>
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
