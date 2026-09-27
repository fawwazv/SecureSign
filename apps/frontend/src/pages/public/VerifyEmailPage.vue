<template>
  <div class="bg-cream/60">
    <div class="sv-container flex min-h-[calc(100vh-16rem)] items-center justify-center py-12">
      <Card class="w-full max-w-md" title="Verifikasi email" :subtitle="subtitle">
        <div class="space-y-4">
          <Alert v-if="status === 'success'" variant="success" title="Email terverifikasi">
            Akun Anda aktif. Silakan masuk untuk mulai menggunakan SignVault.
          </Alert>
          <Alert v-else-if="status === 'sent'" variant="info" title="Tautan verifikasi dikirim">
            Kami mengirim email verifikasi ke <strong>{{ email }}</strong>. Tautan kedaluwarsa
            dalam 24 jam dan hanya sekali pakai.
          </Alert>
          <Alert v-else-if="status === 'error'" variant="error" title="Verifikasi gagal">
            {{ error || 'Token tidak valid atau sudah kedaluwarsa.' }}
          </Alert>

          <div v-if="status === 'sent' || status === 'error'" class="flex flex-col gap-2">
            <Button variant="secondary" block :loading="resending" @click="resend">
              Kirim ulang email verifikasi
            </Button>
            <p v-if="resent" class="text-center text-sm text-[#1B7A3D]">Email terkirim ulang.</p>
          </div>

          <div class="flex flex-col gap-2">
            <RouterLink v-if="status === 'success'" to="/login">
              <Button block>Masuk sekarang</Button>
            </RouterLink>
            <RouterLink to="/" class="text-center text-sm text-deep-blue hover:underline">
              Kembali ke beranda
            </RouterLink>
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Alert, Button, Card } from '@/components/ui'
import { authService } from '@/services/authService'
import { toApiMessage } from '@/services/apiClient'

const route = useRoute()
const email = computed(() => (typeof route.query.email === 'string' ? route.query.email : ''))
const hasToken = computed(() => typeof route.query.token === 'string' && route.query.token.length > 0)

// Status awal: success bila ada token (dikonfirmasi server/BE via Supabase redirect),
// sent bila baru register, error bila token invalid (disimulasikan dari query).
const status = ref<'sent' | 'success' | 'error'>(
  route.query.verified === '1' || (hasToken.value && route.query.error !== '1') ? 'success' : hasToken.value ? 'error' : 'sent',
)
const subtitle = computed(() =>
  status.value === 'success' ? 'Akun Anda sudah aktif.' : 'Satu langkah lagi sebelum Anda bisa masuk.',
)
const error = ref(typeof route.query.message === 'string' ? route.query.message : '')
const resending = ref(false)
const resent = ref(false)

async function resend() {
  if (!email.value) return
  resending.value = true
  try {
    await authService.resendVerification(email.value)
    resent.value = true
  } catch (e) {
    error.value = toApiMessage(e, 'Gagal mengirim ulang email.')
    status.value = 'error'
  } finally {
    resending.value = false
  }
}
</script>
