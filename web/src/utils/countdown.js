import { computed, onMounted, onUnmounted, ref } from 'vue'

export function useCountdown(endTime) {
  const left = ref(0)
  let timer = null

  const tick = () => {
    const end = new Date(endTime).getTime()
    left.value = Number.isNaN(end) ? 0 : Math.max(0, end - Date.now())
  }

  onMounted(() => {
    tick()
    timer = setInterval(tick, 1000)
  })
  onUnmounted(() => clearInterval(timer))

  const parts = computed(() => {
    const total = Math.floor(left.value / 1000)
    const pad = (n) => String(n).padStart(2, '0')
    return {
      hours: pad(Math.floor(total / 3600)),
      minutes: pad(Math.floor((total % 3600) / 60)),
      seconds: pad(total % 60),
      ended: left.value <= 0,
    }
  })

  return { left, parts }
}
