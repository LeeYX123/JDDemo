<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: { type: String, default: 'arrow-right' },
  size: { type: [Number, String], default: 16 },
  stroke: { type: [Number, String], default: 1.8 },
})

const ICONS = {
  search: ['M20 20l-4.4-4.4', 'M11 18.4a7.4 7.4 0 1 0 0-14.8 7.4 7.4 0 0 0 0 14.8Z'],
  cart: [
    'M2.5 3.5h2.2l2.2 11.2a1.8 1.8 0 0 0 1.8 1.4h7.9a1.8 1.8 0 0 0 1.8-1.4L20 7.4H5.6',
    'M9.8 20.4h.1M17 20.4h.1',
  ],
  user: ['M20 21a8 8 0 0 0-16 0', 'M12 12.6a4.1 4.1 0 1 0 0-8.2 4.1 4.1 0 0 0 0 8.2Z'],
  'arrow-right': ['M4 12h15', 'M13 6l6 6-6 6'],
  'arrow-left': ['M20 12H5', 'M11 6l-6 6 6 6'],
  'chevron-right': ['M9 5l7 7-7 7'],
  'chevron-left': ['M15 5l-7 7 7 7'],
  'chevron-down': ['M5 9l7 7 7-7'],
  check: ['M4 12.5l5 5L20 6.5'],
  location: [
    'M12 21s7-5.6 7-11a7 7 0 1 0-14 0c0 5.4 7 11 7 11Z',
    'M12 12.6a2.6 2.6 0 1 0 0-5.2 2.6 2.6 0 0 0 0 5.2Z',
  ],
  plus: ['M12 5v14M5 12h14'],
  minus: ['M5 12h14'],
  trash: ['M4 7h16', 'M9 7V4.8h6V7', 'M6.5 7l1 13h9l1-13', 'M10 11v5M14 11v5'],
  close: ['M6 6l12 12M18 6L6 18'],
  shield: ['M12 3l8 3v6c0 5-3.4 8-8 9-4.6-1-8-4-8-9V6l8-3Z', 'M8.6 12l2.4 2.4 4.4-4.6'],
  truck: [
    'M2.5 6.5h11v10h-11z',
    'M13.5 10h4l3 3v3.5h-7z',
    'M7 19.5a1.8 1.8 0 1 0 0-3.6 1.8 1.8 0 0 0 0 3.6ZM17 19.5a1.8 1.8 0 1 0 0-3.6 1.8 1.8 0 0 0 0 3.6Z',
  ],
  service: [
    'M4 14v-2a8 8 0 0 1 16 0v2',
    'M4 14h2.5v5H4zM17.5 14H20v5h-2.5z',
    'M19 19v.6a2.4 2.4 0 0 1-2.4 2.4H13',
  ],
  coupon: ['M3 7h18v4a2 2 0 0 0 0 4v3H3v-3a2 2 0 0 0 0-4V7Z', 'M9 7v12', 'M13 10h4M13 13h4'],
  clock: ['M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z', 'M12 7v5.4l3.4 2'],
  phone: [
    'M6.5 3h3l1.5 4-2 1.5a11 11 0 0 0 6 6L16.5 12l4 1.5v3a2 2 0 0 1-2.2 2A16 16 0 0 1 4 4.2 2 2 0 0 1 6 3Z',
  ],
  comment: ['M4 4h16v12H9l-5 4V4Z', 'M8 9h8M8 12h5'],
  star: ['M12 3.5l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17.5 6.6 20.4l1-6.1L3.2 10l6.1-.9L12 3.5Z'],
  crown: ['M3 8l4.5 3L12 5l4.5 6L21 8l-1.6 10H4.6L3 8Z'],
  refresh: ['M20 11a8 8 0 1 0-2.3 6.3', 'M20 5v6h-6'],
  play: ['M8 5l11 7-11 7V5Z'],
  bag: ['M5 7h14l1 13H4L5 7Z', 'M9 7V5a3 3 0 0 1 6 0v2'],
  card: ['M3 5h18v14H3z', 'M3 10h18M7 15h3'],
  wallet: ['M3 6h16a2 2 0 0 1 2 2v10H3V6Z', 'M21 10h-5a2 2 0 0 0 0 4h5'],
  edit: ['M4 20h4l10-10-4-4L4 16v4Z', 'M14 6l4 4'],
  filter: ['M3 5h18l-7 8v6l-4 2v-8L3 5Z'],
  heart: ['M12 20s-7.5-4.7-7.5-10a4.5 4.5 0 0 1 8-2.8A4.5 4.5 0 0 1 20.5 10c0 5.3-8.5 10-8.5 10Z'],
}

const paths = computed(() => ICONS[props.name] || ICONS['arrow-right'])
</script>

<template>
  <svg
    class="icon"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    :stroke-width="stroke"
    stroke="currentColor"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path v-for="(d, i) in paths" :key="i" :d="d" />
  </svg>
</template>
