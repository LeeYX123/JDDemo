<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

defineProps({
  categories: { type: Array, default: () => [] },
})

const router = useRouter()
const active = ref(-1)

function go(category) {
  router.push({ path: '/search', query: { category: category.id } })
}
</script>

<template>
  <aside class="cat-menu" @mouseleave="active = -1">
    <ul class="cat-list">
      <li
        v-for="(cat, i) in categories"
        :key="cat.id"
        class="cat-row"
        @mouseenter="active = i"
        @click="go(cat)"
      >
        <b>{{ cat.name }}</b>
        <span class="cat-sub">{{
          (cat.children || [])
            .slice(0, 3)
            .map((c) => c.name)
            .join(' / ')
        }}</span>
        <span class="cat-arrow">›</span>
      </li>
    </ul>

    <div v-if="active > -1 && categories[active]" class="cat-pop" @mouseenter="active = active">
      <div v-for="second in categories[active].children" :key="second.id" class="cat-pop-col">
        <h4>
          <a @click.stop="go(second)">{{ second.name }} ›</a>
        </h4>
        <ul>
          <li v-for="third in second.children" :key="third.id">
            <a @click.stop="go(third)">{{ third.name }}</a>
          </li>
        </ul>
      </div>
      <div class="cat-pop-tip">共 {{ categories[active].children.length }} 个二级类目</div>
    </div>
  </aside>
</template>
