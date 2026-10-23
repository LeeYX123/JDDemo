<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import PageHead from '../../components/PageHead.vue'
import { api } from '../../api'

const loading = ref(false)
const tree = ref([])
const keyword = ref('')
const treeRef = ref(null)

const visible = ref(false)
const saving = ref(false)
const mode = ref('create')
const editingId = ref(null)
const parentInfo = ref(null)
const form = reactive({ name: '', sort: 0, icon: '▦' })

async function load() {
  loading.value = true
  try {
    tree.value = (await api.get('/console/categories/')) || []
  } finally {
    loading.value = false
  }
}

function openCreate(parent) {
  mode.value = 'create'
  editingId.value = null
  parentInfo.value = parent
  Object.assign(form, { name: '', sort: 0, icon: parent?.icon && parent.level === 1 ? parent.icon : '▦' })
  visible.value = true
}

function openEdit(node) {
  mode.value = 'edit'
  editingId.value = node.id
  parentInfo.value = node.parent ? { name: '上级类目' } : null
  Object.assign(form, { name: node.name, sort: node.sort || 0, icon: node.icon || '▦' })
  visible.value = true
}

async function save() {
  if (!form.name.trim()) return ElMessage.warning('请填写类目名称')
  saving.value = true
  try {
    if (mode.value === 'create') {
      await api.post('/console/categories/', {
        name: form.name.trim(),
        parent: parentInfo.value?.id || null,
        sort: Number(form.sort) || 0,
        icon: form.icon,
      })
      ElMessage.success('类目已新增，前台导航即时生效')
    } else {
      await api.patch(`/console/categories/${editingId.value}/`, {
        name: form.name.trim(),
        sort: Number(form.sort) || 0,
      })
      ElMessage.success('类目已更新')
    }
    visible.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function toggle(node) {
  await api.patch(`/console/categories/${node.id}/`, { enabled: !node.enabled })
  ElMessage.success(node.enabled ? '类目已停用' : '类目已启用')
  load()
}

async function remove(node) {
  try {
    await ElMessageBox.confirm(`删除「${node.name}」后不可恢复，且要求其下无子类目、无商品。`, '删除类目', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await api.del(`/console/categories/${node.id}/`)
    ElMessage.success('类目已删除')
    load()
  } catch {
    /* 错误信息由请求层提示（子类目/商品保护） */
  }
}

const levelText = (level) => ['', '一级', '二级', '三级'][level] || ''

function filterNode(value, data) {
  if (!value) return true
  return data.name.includes(value)
}

watch(keyword, (value) => treeRef.value?.filter(value))

onMounted(load)
</script>

<template>
  <div>
    <PageHead title="类目管理" desc="三级类目树驱动前台左侧导航；停用后前台立即隐藏，删除受子类目与商品保护">
      <template #actions>
        <el-input v-model="keyword" placeholder="搜索类目名" clearable style="width: 200px" />
        <el-button type="primary" @click="openCreate(null)">新增一级类目</el-button>
      </template>
    </PageHead>

    <section v-loading="loading" class="panel">
      <div class="panel-head">
        <h3>类目树</h3>
        <span class="right tip">共 {{ tree.length }} 个一级类目</span>
      </div>
      <div class="panel-body" style="padding: 10px 18px 20px">
        <el-tree
          ref="treeRef"
          :data="tree"
          node-key="id"
          :props="{ label: 'name', children: 'children' }"
          default-expand-all
          :expand-on-click-node="false"
          :filter-node-method="filterNode"
        >
          <template #default="{ data }">
            <div class="cat-node" :class="{ 'is-off': !data.enabled }">
              <span class="cat-name">{{ data.name }}</span>
              <span class="cat-meta">{{ levelText(data.level) }}</span>
              <el-tag v-if="!data.enabled" size="small" type="info" effect="plain">已停用</el-tag>
              <span v-if="data.product_count" class="cat-meta">· {{ data.product_count }} 个商品</span>
              <span class="cat-ops">
                <el-button
                  v-if="data.level < 3"
                  link
                  type="primary"
                  size="small"
                  @click.stop="openCreate(data)"
                >
                  新增子类目
                </el-button>
                <el-button link size="small" @click.stop="openEdit(data)">编辑</el-button>
                <el-button
                  link
                  :type="data.enabled ? 'warning' : 'success'"
                  size="small"
                  @click.stop="toggle(data)"
                >
                  {{ data.enabled ? '停用' : '启用' }}
                </el-button>
                <el-button link type="danger" size="small" @click.stop="remove(data)">删除</el-button>
              </span>
            </div>
          </template>
        </el-tree>
      </div>
    </section>

    <el-dialog
      v-model="visible"
      :title="mode === 'create' ? `新增类目${parentInfo ? ` · 上级：${parentInfo.name}` : ''}` : '编辑类目'"
      width="440px"
    >
      <el-form label-position="top">
        <el-form-item label="类目名称" required>
          <el-input v-model="form.name" maxlength="20" show-word-limit placeholder="例：手机通讯" />
        </el-form-item>
        <div class="form-grid">
          <el-form-item label="排序值">
            <el-input-number v-model="form.sort" :min="0" :max="999" style="width: 100%" />
          </el-form-item>
          <el-form-item label="图标字符">
            <el-input v-model="form.icon" maxlength="4" />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
