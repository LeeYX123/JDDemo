<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import PageHead from '../../components/PageHead.vue'
import { api } from '../../api'

const tab = ref('banner')
const loading = ref(false)
const banners = ref([])
const floors = ref([])
const notices = ref([])
const roots = ref([])

const visible = ref(false)
const saving = ref(false)
const editingId = ref(null)

const bannerForm = reactive({
  title: '',
  subtitle: '',
  color: '#ffe7e5',
  image_seed: 1,
  link: '/search',
  enabled: true,
  sort: 0,
})
const floorForm = reactive({
  name: '',
  subtitle: '',
  category: null,
  tabsText: '热门推荐,新品上架,价格亲民',
  color: '#e1251b',
  enabled: true,
  sort: 0,
})
const noticeForm = reactive({ title: '', category: '快报', enabled: true, sort: 0 })

const COLOR_PRESETS = ['#ffe7e5', '#e8f0ff', '#e8f8ef', '#fff4dd', '#f2eaff', '#e7f7f8', '#fdebf4', '#eff2f6']
const dialogTitle = computed(() => {
  const names = { banner: '轮播图', floor: '楼层', notice: '快报' }
  return `${editingId.value ? '编辑' : '新增'}${names[tab.value]}`
})

async function load() {
  loading.value = true
  try {
    const [b, f, n] = await Promise.all([
      api.get('/console/banners/'),
      api.get('/console/floors/'),
      api.get('/console/notices/'),
    ])
    banners.value = b || []
    floors.value = f || []
    notices.value = n || []
  } finally {
    loading.value = false
  }
}

async function loadRoots() {
  roots.value = (await api.get('/console/categories/')) || []
}

function openCreate() {
  editingId.value = null
  if (tab.value === 'banner') {
    Object.assign(bannerForm, {
      title: '',
      subtitle: '',
      color: '#ffe7e5',
      image_seed: 1,
      link: '/search',
      enabled: true,
      sort: banners.value.length,
    })
  } else if (tab.value === 'floor') {
    Object.assign(floorForm, {
      name: '',
      subtitle: '',
      category: null,
      tabsText: '热门推荐,新品上架,价格亲民',
      color: '#e1251b',
      enabled: true,
      sort: floors.value.length,
    })
    if (!roots.value.length) loadRoots()
  } else {
    Object.assign(noticeForm, { title: '', category: '快报', enabled: true, sort: notices.value.length })
  }
  visible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  if (tab.value === 'banner') Object.assign(bannerForm, row)
  else if (tab.value === 'floor') {
    Object.assign(floorForm, { ...row, tabsText: (row.tabs || []).join(',') })
    if (!roots.value.length) loadRoots()
  } else Object.assign(noticeForm, row)
  visible.value = true
}

async function save() {
  saving.value = true
  try {
    if (tab.value === 'banner') {
      const payload = { ...bannerForm }
      editingId.value
        ? await api.patch(`/console/banners/${editingId.value}/`, payload)
        : await api.post('/console/banners/', payload)
    } else if (tab.value === 'floor') {
      const payload = {
        name: floorForm.name,
        subtitle: floorForm.subtitle,
        category: floorForm.category,
        tabs: floorForm.tabsText
          .split(/[,，]/)
          .map((t) => t.trim())
          .filter(Boolean),
        color: floorForm.color,
        enabled: floorForm.enabled,
        sort: floorForm.sort,
      }
      editingId.value
        ? await api.patch(`/console/floors/${editingId.value}/`, payload)
        : await api.post('/console/floors/', payload)
    } else {
      const payload = { ...noticeForm }
      editingId.value
        ? await api.patch(`/console/notices/${editingId.value}/`, payload)
        : await api.post('/console/notices/', payload)
    }
    ElMessage.success('已保存，前台刷新后立即生效')
    visible.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function toggle(row, type) {
  await api.patch(`/console/${type}s/${row.id}/`, { enabled: !row.enabled })
  ElMessage.success(row.enabled ? '已下线' : '已上线')
  load()
}

async function remove(row, type, name) {
  try {
    await ElMessageBox.confirm(`删除「${name}」后不可恢复，前台将立即不再展示。`, '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  await api.del(`/console/${type}s/${row.id}/`)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>

<template>
  <div>
    <PageHead title="内容运营" desc="轮播图、首页楼层与快报均实时驱动买家端首页，保存后刷新前台即可看到">
      <template #actions>
        <el-button @click="load">刷新</el-button>
        <el-button type="primary" @click="openCreate">
          新增{{ tab === 'banner' ? '轮播' : tab === 'floor' ? '楼层' : '快报' }}
        </el-button>
      </template>
    </PageHead>

    <el-tabs v-model="tab">
      <el-tab-pane label="轮播图" name="banner">
        <section v-loading="loading" class="panel">
          <div class="panel-head">
            <h3>首屏轮播（590 × 470）</h3>
            <span class="right tip">共 {{ banners.length }} 张</span>
          </div>
          <div class="panel-body">
            <div class="content-grid">
              <div v-for="item in banners" :key="item.id" class="mini-card">
                <div class="mini-head">
                  <span class="swatch" :style="{ background: item.color }" />
                  <b>{{ item.title }}</b>
                  <el-tag :type="item.enabled ? 'success' : 'info'" size="small" effect="light">
                    {{ item.enabled ? '展示中' : '已下线' }}
                  </el-tag>
                </div>
                <p>{{ item.subtitle || '无副标题' }}</p>
                <p>跳转：{{ item.link }} · 排序 {{ item.sort }} · 配色 {{ item.image_seed }}</p>
                <div class="mini-foot">
                  <el-button size="small" @click="openEdit(item)">编辑</el-button>
                  <el-button
                    size="small"
                    :type="item.enabled ? 'warning' : 'success'"
                    plain
                    @click="toggle(item, 'banner')"
                  >
                    {{ item.enabled ? '下线' : '上线' }}
                  </el-button>
                  <el-button size="small" type="danger" plain @click="remove(item, 'banner', item.title)">
                    删除
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </section>
      </el-tab-pane>

      <el-tab-pane label="首页楼层" name="floor">
        <section v-loading="loading" class="panel">
          <div class="panel-head">
            <h3>商品楼层</h3>
            <span class="right tip">共 {{ floors.length }} 个楼层</span>
          </div>
          <div class="panel-body">
            <div class="content-grid">
              <div v-for="item in floors" :key="item.id" class="mini-card">
                <div class="mini-head">
                  <span class="swatch" :style="{ background: item.color }" />
                  <b>{{ item.name }}</b>
                  <el-tag :type="item.enabled ? 'success' : 'info'" size="small" effect="light">
                    {{ item.enabled ? '展示中' : '已下线' }}
                  </el-tag>
                </div>
                <p>{{ item.subtitle || '无副标题' }}</p>
                <p>类目：{{ item.category_name || '未绑定' }} · 排序 {{ item.sort }}</p>
                <p>Tab：{{ (item.tabs || []).join(' / ') || '默认三个 Tab' }}</p>
                <div class="mini-foot">
                  <el-button size="small" @click="openEdit(item)">编辑</el-button>
                  <el-button
                    size="small"
                    :type="item.enabled ? 'warning' : 'success'"
                    plain
                    @click="toggle(item, 'floor')"
                  >
                    {{ item.enabled ? '下线' : '上线' }}
                  </el-button>
                  <el-button size="small" type="danger" plain @click="remove(item, 'floor', item.name)">
                    删除
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </section>
      </el-tab-pane>

      <el-tab-pane label="快报" name="notice">
        <section v-loading="loading" class="panel">
          <div class="panel-head">
            <h3>首屏快报</h3>
            <span class="right tip">共 {{ notices.length }} 条</span>
          </div>
          <div class="panel-body">
            <div class="content-grid">
              <div v-for="item in notices" :key="item.id" class="mini-card">
                <div class="mini-head">
                  <b>{{ item.title }}</b>
                  <el-tag :type="item.enabled ? 'success' : 'info'" size="small" effect="light">
                    {{ item.enabled ? '展示中' : '已下线' }}
                  </el-tag>
                </div>
                <p>分类：{{ item.category }} · 排序 {{ item.sort }}</p>
                <div class="mini-foot">
                  <el-button size="small" @click="openEdit(item)">编辑</el-button>
                  <el-button
                    size="small"
                    :type="item.enabled ? 'warning' : 'success'"
                    plain
                    @click="toggle(item, 'notice')"
                  >
                    {{ item.enabled ? '下线' : '上线' }}
                  </el-button>
                  <el-button size="small" type="danger" plain @click="remove(item, 'notice', item.title)">
                    删除
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </section>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="visible" :title="dialogTitle" width="520px">
      <el-form v-if="tab === 'banner'" label-position="top">
        <el-form-item label="主标题" required>
          <el-input v-model="bannerForm.title" maxlength="40" />
        </el-form-item>
        <el-form-item label="副标题">
          <el-input v-model="bannerForm.subtitle" maxlength="60" />
        </el-form-item>
        <div class="form-grid">
          <el-form-item label="背景配色">
            <el-select v-model="bannerForm.color" style="width: 100%">
              <el-option v-for="color in COLOR_PRESETS" :key="color" :label="color" :value="color">
                <span
                  style="
                    display: inline-block;
                    width: 12px;
                    height: 12px;
                    border-radius: 3px;
                    margin-right: 8px;
                  "
                  :style="{ background: color }"
                />
                {{ color }}
              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="占位图配色">
            <el-select v-model="bannerForm.image_seed" style="width: 100%">
              <el-option v-for="n in 8" :key="n" :label="`配色 ${n}`" :value="n" />
            </el-select>
          </el-form-item>
          <el-form-item label="跳转路径">
            <el-input v-model="bannerForm.link" placeholder="/search 或 /item/1" />
          </el-form-item>
          <el-form-item label="排序">
            <el-input-number v-model="bannerForm.sort" :min="0" :max="99" style="width: 100%" />
          </el-form-item>
        </div>
        <el-form-item label="是否展示">
          <el-switch v-model="bannerForm.enabled" />
        </el-form-item>
      </el-form>

      <el-form v-else-if="tab === 'floor'" label-position="top">
        <el-form-item label="楼层标题" required>
          <el-input v-model="floorForm.name" maxlength="20" />
        </el-form-item>
        <el-form-item label="副标题">
          <el-input v-model="floorForm.subtitle" maxlength="40" />
        </el-form-item>
        <div class="form-grid">
          <el-form-item label="绑定一级类目">
            <el-select
              v-model="floorForm.category"
              clearable
              style="width: 100%"
              placeholder="不绑定则展示全站"
            >
              <el-option v-for="root in roots" :key="root.id" :label="root.name" :value="root.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="强调色">
            <el-select v-model="floorForm.color" style="width: 100%">
              <el-option label="京东红 #e1251b" value="#e1251b" />
              <el-option label="深红 #c81623" value="#c81623" />
              <el-option label="橙 #ff6f00" value="#ff6f00" />
              <el-option label="蓝 #1d64d8" value="#1d64d8" />
            </el-select>
          </el-form-item>
          <el-form-item label="Tab 文案（逗号分隔）" class="span2">
            <el-input v-model="floorForm.tabsText" placeholder="热门推荐,新品上架,价格亲民" />
          </el-form-item>
          <el-form-item label="排序">
            <el-input-number v-model="floorForm.sort" :min="0" :max="99" style="width: 100%" />
          </el-form-item>
        </div>
        <el-form-item label="是否展示">
          <el-switch v-model="floorForm.enabled" />
        </el-form-item>
      </el-form>

      <el-form v-else label-position="top">
        <el-form-item label="快报标题" required>
          <el-input v-model="noticeForm.title" maxlength="60" />
        </el-form-item>
        <div class="form-grid">
          <el-form-item label="分类">
            <el-input v-model="noticeForm.category" maxlength="10" />
          </el-form-item>
          <el-form-item label="排序">
            <el-input-number v-model="noticeForm.sort" :min="0" :max="99" style="width: 100%" />
          </el-form-item>
        </div>
        <el-form-item label="是否展示">
          <el-switch v-model="noticeForm.enabled" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
