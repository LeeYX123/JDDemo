<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: '-' },
  unit: { type: String, default: '' },
  hint: { type: String, default: '' },
  hintType: { type: String, default: '' },
})
</script>

<template>
  <div class="stat-card">
    <span>{{ label }}</span>
    <strong>
      <em v-if="unit">{{ unit }}</em
      >{{ value }}
    </strong>
    <small v-if="hint" :class="hintType">{{ hint }}</small>
  </div>
</template>
