<template>
  <div class="bg-cream/60">
    <div class="sv-container flex min-h-[calc(100vh-16rem)] items-center justify-center py-12">
      <Card class="w-full max-w-md text-center" title="403 — Akses ditolak">
        <p class="text-slate-600">
          Peran Anda (<strong>{{ roleLabel }}</strong>) tidak memiliki akses ke halaman ini.
        </p>
        <p class="mt-2 text-sm text-slate-500">
          Baru ganti peran (mis. setelah onboarding)? Sesi lama masih membawa peran lama —
          masuk ulang untuk menyegarkan sesi.
        </p>
        <div class="mt-4 flex flex-col gap-2">
          <Button :loading="busy" @click="relogin">Keluar & masuk ulang</Button>
          <RouterLink to="/">
            <Button variant="secondary" block>Kembali ke beranda</Button>
          </RouterLink>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Button, Card } from '@/components/ui'
import { useAuthStore } from '@/stores/authStore'

const router = useRouter()
const store = useAuthStore()
const busy = ref(false)

const roleLabel = computed(() => store.user?.role ?? 'tidak dikenal')

async function relogin() {
  busy.value = true
  try {
    await store.logout()
  } finally {
    busy.value = false
    await router.replace('/login')
  }
}
</script>
