<template>
  <div class="bg-cream/60">
    <div class="sv-container flex min-h-[calc(100vh-16rem)] items-center justify-center py-12">
      <Card class="w-full max-w-md" title="Verifikasi email" :subtitle="subtitle">
        <div class="space-y-4">
          <Alert v-if="status === 'verifying'" variant="info" title="Memverifikasi…">
            Menghubungi server, mohon tunggu.
          </Alert>
          <Alert v-if="status === 'success'" variant="success" title="Email terverifikasi">
            {{ message || 'Akun Anda aktif. Silakan masuk untuk mulai menggunakan SignVault.' }}
          </Alert>
          <Alert v-else-if="status === 'sent'" variant="info" title="Tautan verifikasi dikirim">
            Kami mengirim email verifikasi ke <strong>{{ email }}</strong>. Tautan kedaluwarsa
            dalam 24 jam dan hanya sekali pakai. Buka tautan tersebut, atau tempel token di bawah.
          </Alert>
          <Alert v-else-if="status === 'error'" variant="error" title="Verifikasi gagal">
            {{ message || 'Token tidak valid atau sudah kedaluwarsa.' }}
          </Alert>

          <Input
            v-if="status === 'sent' || status === 'error'"
            id="vtoken" v-model="tokenInput" label="Token verifikasi (opsional)"
            placeholder="Tempel token dari email" :error="''"
          />

          <TurnstileWidget
            v-if="status === 'sent' || status === 'error'"
            ref="turnstileRef"
            @verified="onCaptchaVerified"
            @expired="onCaptchaExpired"
          />
          <p v-if="needCaptcha && !captchaToken" class="text-xs text-slate-500">
            Selesaikan CAPTCHA di atas dulu agar tombol kirim ulang aktif.
          </p>

          <div v-if="email" class="flex flex-col gap-2">
            <Button
              v-if="status !== 'success'"
              variant="secondary" block :loading="busy" :disabled="!canClick"
              @click="isVerifyMode ? doVerify() : resend()"
            >
              {{ isVerifyMode ? 'Verifikasi sekarang' : 'Kirim ulang email verifikasi' }}
            </Button>
            <p v-if="resent" class="text-center text-sm text-[#1B7A3D]">{{ resent }}</p>
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
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Alert, Button, Card, Input } from '@/components/ui'
import TurnstileWidget from '@/components/auth/TurnstileWidget.vue'
import { authService } from '@/services/authService'
import { toApiCode, toApiMessage } from '@/services/apiClient'

const route = useRoute()
const email = computed(() => (typeof route.query.email === 'string' ? route.query.email : ''))
const token = computed(() => (typeof route.query.token === 'string' ? route.query.token : ''))

type Status = 'sent' | 'verifying' | 'success' | 'error'
const status = ref<Status>(route.query.sent === '1' || email.value ? 'sent' : 'sent')
const message = ref('')
const resent = ref('')
const busy = ref(false)
const tokenInput = ref('')
const captchaToken = ref('')
const turnstileRef = ref<InstanceType<typeof TurnstileWidget> | null>(null)
const hasCaptchaKey = computed(() => (import.meta.env.VITE_CAPTCHA_SITE_KEY ?? '').length > 0)
/** Mode tombol: verifikasi pakai token email (tanpa captcha) vs kirim ulang (butuh captcha). */
const isVerifyMode = computed(() => status.value === 'error' || tokenInput.value.trim().length > 0)
const needCaptcha = computed(() => !isVerifyMode.value && hasCaptchaKey.value)
const canClick = computed(() => !busy.value && (!needCaptcha.value || captchaToken.value.length > 0))

function onCaptchaVerified(token: string) {
  captchaToken.value = token
}

function onCaptchaExpired() {
  captchaToken.value = ''
}

const subtitle = computed(() =>
  status.value === 'success' ? 'Akun Anda sudah aktif.' : 'Satu langkah lagi sebelum Anda bisa masuk.',
)

async function doVerify(usingToken?: string) {
  const t = (usingToken ?? tokenInput.value ?? token.value).trim()
  if (!email.value || !t) {
    status.value = 'error'
    message.value = 'Email dan token wajib ada. Buka tautan dari email atau kirim ulang.'
    return
  }
  busy.value = true
  status.value = 'verifying'
  try {
    message.value = await authService.verifyEmail({ email: email.value, token: t })
    status.value = 'success'
  } catch (e) {
    status.value = 'error'
    message.value = toApiMessage(e, 'Token tidak valid atau sudah kedaluwarsa.')
  } finally {
    busy.value = false
  }
}

async function resend() {
  if (!email.value) return
  if (needCaptcha.value && !captchaToken.value) return
  busy.value = true
  try {
    resent.value = await authService.resendVerification(
      email.value,
      captchaToken.value || undefined,
    )
  } catch (e) {
    status.value = 'error'
    message.value = toApiMessage(e, 'Gagal mengirim ulang email.')
    if (toApiCode(e) === 'CAPTCHA_FAILED') {
      captchaToken.value = ''
      turnstileRef.value?.reset()
    }
  } finally {
    busy.value = false
  }
}

// Link email BE: /verify-email?email=...&token=... → verifikasi otomatis.
onMounted(() => {
  if (email.value && token.value) void doVerify(token.value)
})
</script>
