<script setup>
import { computed } from 'vue'

const props = defineProps({
  seed: { type: [Number, String], default: 1 },
  size: { type: String, default: 'md' },
  title: { type: String, default: '商品图' },
  emoji: { type: String, default: '' },
})

const EMOJIS = ['📱', '🎧', '🧊', '🍳', '👟', '💄', '🍎', '🧸']
const index = computed(() => Number(props.seed || 1) % 8)
const glyph = computed(() => props.emoji || EMOJIS[index.value])
</script>

<template>
  <div class="product-art" :class="[`art-${index}`, `art-size-${size}`]" role="img" :aria-label="title">
    <span class="art-ring" />
    <span class="art-glyph">{{ glyph }}</span>
    <small class="art-label">JD SELECT</small>
  </div>
</template>
