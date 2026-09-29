<template>
  <div class="bg-cream/60">
    <div class="sv-container flex min-h-[calc(100vh-16rem)] items-center justify-center py-12">
      <Card class="w-full max-w-md" title="Memproses login Google" subtitle="Mohon tunggu sebentar.">
        <div class="space-y-4">
          <Alert v-if="error" variant="error" title="Login Google gagal">{{ error }}</Alert>
          <p v-else class="text-sm text-slate-600">Memverifikasi akun Google Anda…</p>
          <RouterLink v-if="error" to="/login" class="block text-center text-sm font-semibold text-deep-blue hover:underline">
            Kembali ke halaman masuk
          </RouterLink>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Alert, Card } from '@/components/ui'
import { useAuthStore } from '@/stores/authStore'

const route = useRoute()
const router = useRouter()
const error = ref('')

onMounted(async () => {
  const store = useAuthStore()
  // GIS callback standar mengirim `credential` (id_token). Dukung via query (?credential=)
  // maupun hash (#credential=) agar fleksibel terhadap konfigurasi GIS.
  const fromQuery = typeof route.query.credential === 'string' ? route.query.credential : ''
  const hashMatch = typeof window !== 'undefined' ? window.location.hash.match(/credential=([^&]+)/) : null
  const idToken = fromQuery || (hashMatch ? decodeURIComponent(hashMatch[1]) : '')
  if (!idToken) {
    error.value = 'Token Google tidak ditemukan. Silakan ulangi dari halaman masuk.'
    return
  }
  try {
    const { needsOnboarding } = await store.loginWithGoogle(idToken)
    if (needsOnboarding) {
      await router.replace('/onboarding')
      return
    }
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : ''
    if (redirect) await router.replace(redirect)
    else await router.replace(store.roleHome())
  } catch {
    error.value = store.error || 'Verifikasi Google gagal. Coba lagi.'
  }
})
</script>
