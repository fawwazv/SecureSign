<template>
  <div>
    <div ref="boxRef"></div>
    <p v-if="!hasKey" class="text-xs text-slate-500">
      CAPTCHA belum dikonfigurasi (VITE_CAPTCHA_SITE_KEY kosong) — mode dev, form tetap bisa dikirim.
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const props = withDefaults(
  defineProps<{
    siteKey?: string
    theme?: 'light' | 'dark' | 'auto'
  }>(),
  { siteKey: '', theme: 'auto' },
)

const emit = defineEmits<{
  verified: [token: string]
  expired: []
  error: [message: string]
}>()

const boxRef = ref<HTMLDivElement | null>(null)
const widgetId = ref<string | number | null>(null)
const hasKey = computed(() => (props.siteKey || import.meta.env.VITE_CAPTCHA_SITE_KEY || '').length > 0)

type TurnstileApi = {
  render: (el: HTMLElement, o: Record<string, unknown>) => string | number
  reset: (id?: string | number) => void
  remove?: (id?: string | number) => void
}

function api(): TurnstileApi | undefined {
  return (window as unknown as { turnstile?: TurnstileApi }).turnstile
}

onMounted(() => {
  const key = props.siteKey || import.meta.env.VITE_CAPTCHA_SITE_KEY || ''
  const t = api()
  if (!key || !t || !boxRef.value) return // mode dev: tidak render, biarkan parent submit
  try {
    widgetId.value = t.render(boxRef.value, {
      sitekey: key,
      theme: props.theme,
      callback: (token: string) => emit('verified', token),
      'expired-callback': () => emit('expired'),
      'error-callback': () => emit('error', 'Verifikasi CAPTCHA gagal. Muat ulang dan coba lagi.'),
    })
  } catch {
    emit('error', 'Gagal memuat CAPTCHA.')
  }
})

onBeforeUnmount(() => {
  try {
    if (widgetId.value !== null) api()?.remove?.(widgetId.value)
  } catch {
    /* abaikan */
  }
})

function reset() {
  try {
    if (widgetId.value !== null) api()?.reset(widgetId.value)
  } catch {
    /* abaikan */
  }
}

defineExpose({ reset })
</script>
