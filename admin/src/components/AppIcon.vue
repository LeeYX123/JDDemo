<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: { type: String, default: 'grid' },
  size: { type: [Number, String], default: 18 },
})

const ICONS = {
  grid: ['M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z'],
  box: ['M3.5 7.5 12 3.5l8.5 4v9L12 20.5l-8.5-4z', 'M3.5 7.5 12 11.5l8.5-4M12 11.5v9'],
  list: ['M8 6h12M8 12h12M8 18h12', 'M4 6h.1M4 12h.1M4 18h.1'],
  refresh: ['M20 11a8 8 0 1 0-2.3 6.3', 'M20 5v6h-6'],
  shop: ['M4 9h16v11H4z', 'M3 9l1.6-4.5h14.8L21 9', 'M9 20v-6h6v6'],
  tree: ['M4 4h6v4H4zM14 10h6v4h-6zM14 17h6v4h-6z', 'M7 8v11h7M7 12h7'],
  star: ['M12 3.6l2.6 5.4 5.9.9-4.3 4.1 1 5.9L12 17.1 6.8 19.9l1-5.9L3.5 9.9l5.9-.9z'],
  user: ['M20 21a8 8 0 0 0-16 0', 'M12 12.5a4 4 0 1 0 0-8 4 4 0 0 0 0 8z'],
  bell: ['M18 15v-4a6 6 0 1 0-12 0v4l-2 3h16z', 'M10 21h4'],
  logout: ['M15 4h4a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1h-4', 'M10 8l-4 4 4 4M6 12h10'],
  arrow: ['M5 12h13', 'M12 6l6 6-6 6'],
  cart: ['M3 4h2l2.2 10.4A1.8 1.8 0 0 0 9 16h8.4a1.8 1.8 0 0 0 1.8-1.5L21 7H6'],
  clock: ['M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z', 'M12 7v5.2l3.4 2'],
  check: ['M4 12.5l5 5L20 6.5'],
  money: ['M3 6h18v12H3z', 'M3 10h18M7 15h4'],
}

const paths = computed(() => ICONS[props.name] || ICONS.grid)
</script>

<template>
  <svg
    class="ico"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.7"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path v-for="(d, i) in paths" :key="i" :d="d" />
  </svg>
</template>

<style scoped>
.ico {
  display: block;
  flex: none;
}
</style>
