<script setup>
import ProductImage from './ProductImage.vue'

defineProps({
  product: { type: Object, required: true },
  specKeys: { type: Array, default: () => [] },
  specValues: { type: Function, required: true },
  modelValue: { type: String, default: 'detail' },
})

const emit = defineEmits(['update:modelValue'])

const TABS = [
  { key: 'detail', label: '商品介绍' },
  { key: 'specs', label: '规格参数' },
  { key: 'reviews', label: '商品评价' },
  { key: 'service', label: '售后保障' },
]

function select(key) {
  emit('update:modelValue', key)
}

const stars = (n) => '★'.repeat(n)
</script>

<template>
  <section class="item-detail">
    <div class="detail-tabs">
      <button
        v-for="item in TABS"
        :key="item.key"
        :class="{ on: modelValue === item.key }"
        @click="select(item.key)"
      >
        {{ item.label }}
        <span v-if="item.key === 'reviews'" class="tab-count">{{ product.review_count }}</span>
      </button>
    </div>

    <div v-if="modelValue === 'detail'" class="detail-body detail-desc">
      <div class="desc-art">
        <ProductImage :seed="product.image_seed" size="hero" :title="product.title" />
      </div>
      <div class="desc-text">
        <h3>{{ product.title }}</h3>
        <p v-for="line in (product.detail || '').split('\n')" :key="line">{{ line }}</p>
        <ul>
          <li v-for="tag in product.tag_list" :key="tag">· {{ tag }} 品质认证</li>
          <li>· 京东物流配送，部分区域次日达</li>
          <li>· 7 天无理由退货，全国联保</li>
        </ul>
      </div>
    </div>

    <div v-else-if="modelValue === 'specs'" class="detail-body">
      <table class="spec-table">
        <tbody>
          <tr>
            <th>商品名称</th>
            <td>{{ product.title }}</td>
          </tr>
          <tr>
            <th>品牌</th>
            <td>{{ product.brand_name }}</td>
          </tr>
          <tr>
            <th>类目</th>
            <td>{{ product.category_path?.map((c) => c.name).join(' / ') }}</td>
          </tr>
          <tr v-for="key in specKeys" :key="key">
            <th>{{ key }}</th>
            <td>{{ specValues(key).join(' / ') }}</td>
          </tr>
          <tr>
            <th>店铺</th>
            <td>{{ product.shop_name }}</td>
          </tr>
          <tr>
            <th>库存</th>
            <td>{{ product.stock }} 件</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else-if="modelValue === 'reviews'" class="detail-body reviews">
      <div v-if="product.reviews?.length" class="review-list">
        <article v-for="review in product.reviews" :key="review.id" class="review">
          <div class="review-user">
            <span class="avatar" :class="`art-${review.avatar_seed % 8}`">
              {{ review.user_name.slice(0, 1) }}
            </span>
            <div>
              <b>{{ review.user_name }}</b>
              <div class="stars">
                {{ stars(review.rating) }}<i>{{ stars(5 - review.rating) }}</i>
              </div>
            </div>
            <span class="review-date">{{ String(review.created_at).slice(0, 10) }}</span>
          </div>
          <p class="review-content">{{ review.content }}</p>
          <p v-if="review.reply" class="review-reply">商家回复：{{ review.reply }}</p>
        </article>
      </div>
      <div v-else class="empty"><p>该商品还没有评价</p></div>
    </div>

    <div v-else class="detail-body service-body">
      <h3>京东售后服务承诺</h3>
      <p>· 正品保障：所有商品均为品牌正品，支持专柜验货。</p>
      <p>· 7 天无理由退货：签收后 7 天内，商品完好可申请退货。</p>
      <p>· 价格保护：下单后 7 天内降价可申请差额补偿。</p>
      <p>· 全国联保：凭订单号享受品牌官方售后网点服务。</p>
      <p>· 客服支持：7×24 小时在线客服，平均响应 30 秒。</p>
    </div>
  </section>
</template>
