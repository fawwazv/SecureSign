<template>
  <div>
    <div class="flex justify-center">
      <div ref="btnRef" class="max-w-full overflow-hidden"></div>
    </div>
    <p v-if="fallback" class="mt-2 text-center text-xs text-slate-500">
      Tombol Google tidak dapat dimuat (script/client-id belum siap).
      Lanjutkan dengan email + kata sandi.
    </p>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

const props = withDefaults(
  defineProps<{
    text?: 'signin_with' | 'signup_with' | 'continue_with'
    disabled?: boolean
  }>(),
  { text: 'continue_with', disabled: false },
)

const emit = defineEmits<{
  credential: [idToken: string]
  error: [message: string]
}>()

const btnRef = ref<HTMLDivElement | null>(null)
const fallback = ref(false)

function clientId(): string {
  return import.meta.env.VITE_GOOGLE_CLIENT_ID ?? ''
}

onMounted(() => {
  const id = clientId()
  const g = (window as unknown as { google?: unknown }).google as
    | {
        accounts?: {
          id?: {
            initialize?: (o: Record<string, unknown>) => void
            renderButton?: (el: HTMLElement, o: Record<string, unknown>) => void
          }
        }
      }
    | undefined
  if (!id || !g?.accounts?.id?.initialize || !g?.accounts?.id?.renderButton || !btnRef.value) {
    fallback.value = true
    return
  }
  try {
    g.accounts.id.initialize({
      client_id: id,
      callback: (resp: { credential?: string }) => {
        if (resp?.credential) emit('credential', resp.credential)
        else emit('error', 'Respons Google kosong. Coba lagi.')
      },
      auto_select: false,
      cancel_on_tap_outside: true,
    })
    g.accounts.id.renderButton(btnRef.value, {
      theme: 'outline',
      size: 'large',
      width: 320,
      text: props.text,
    })
  } catch {
    fallback.value = true
    emit('error', 'Gagal memuat tombol Google.')
  }
})
</script>
