<template>
  <div class="bg-cream/60">
    <div class="sv-container flex min-h-[calc(100vh-16rem)] items-center justify-center py-12">
      <Card class="w-full max-w-md" title="Masuk ke SignVault" subtitle="Gunakan email yang sudah terverifikasi.">
        <form class="space-y-4" novalidate @submit.prevent="onSubmit">
          <Alert v-if="authError" variant="error" title="Gagal masuk">{{ authError }}</Alert>
          <Alert v-if="googleError" variant="error" title="Login Google gagal">{{ googleError }}</Alert>
          <GoogleSignInButton text="signin_with" @credential="onGoogleCredential" />
          <div class="flex items-center gap-3 text-xs text-slate-500" aria-hidden="true">
            <span class="h-px flex-1 bg-slate-200"></span>
            <span>atau dengan email</span>
            <span class="h-px flex-1 bg-slate-200"></span>
          </div>
          <Alert v-if="registered" variant="success" title="Registrasi berhasil">
            Akun dibuat. Cek email untuk verifikasi sebelum masuk.
          </Alert>
          <Input
            id="email"
            v-model="email"
            label="Email"
            type="email"
            autocomplete="email"
            placeholder="nama@perusahaan.id"
            required
            :error="emailError"
            @blur="touched.email = true"
          />
          <Input
            id="password"
            v-model="password"
            label="Kata sandi"
            type="password"
            autocomplete="current-password"
            placeholder="••••••••"
            required
            :error="passwordError"
            @blur="touched.password = true"
          />
          <div class="flex items-center justify-between text-sm">
            <span class="text-slate-500">Belum punya akun?</span>
            <RouterLink to="/register" class="font-semibold text-deep-blue hover:underline">
              Daftar
            </RouterLink>
          </div>
          <Button type="submit" block :loading="isLoading" :disabled="!canSubmit">
            Masuk
          </Button>
          <p class="text-center text-sm">
            <RouterLink to="/forgot-password" class="text-deep-blue hover:underline">
              Lupa kata sandi?
            </RouterLink>
          </p>
        </form>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Alert, Button, Card, Input } from '@/components/ui'
import GoogleSignInButton from '@/components/auth/GoogleSignInButton.vue'
import { useAuth } from '@/composables/useAuth'
import { toApiCode } from '@/services/apiClient'
import { isEmail } from '@/utils/validators'

const route = useRoute()
const router = useRouter()
const { login, isLoading, error: authError } = useAuth()

const email = ref('')
const password = ref('')
const googleError = ref('')
const touched = reactive({ email: false, password: false })
const registered = computed(() => route.query.registered === '1')

const emailError = computed(() => {
  if (!touched.email || email.value === '') return ''
  return isEmail(email.value) ? '' : 'Format email tidak valid.'
})
const passwordError = computed(() => {
  if (!touched.password || password.value === '') return ''
  return password.value.length >= 1 ? '' : 'Kata sandi wajib diisi.'
})
const canSubmit = computed(() => isEmail(email.value) && password.value.length > 0 && !isLoading.value)

async function onSubmit() {
  touched.email = true
  touched.password = true
  if (!canSubmit.value) return
  googleError.value = ''
  try {
    const { useAuthStore } = await import('@/stores/authStore')
    const store = useAuthStore()
    const user = await login(email.value.trim(), password.value)
    void store
    if (store.needsOnboarding) {
      await router.replace('/onboarding')
      return
    }
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : ''
    if (redirect) await router.replace(redirect)
    else if (user.role === 'SUPER_ADMIN') await router.replace('/admin')
    else if (user.role === 'ORG_ADMIN') await router.replace('/org')
    else if (user.role === 'SIGNER') await router.replace('/signer')
    else await router.replace('/')
  } catch (e) {
    // 403 EMAIL_NOT_VERIFIED → arahkan ke verifikasi + tawarkan kirim ulang.
    if (toApiCode(e) === 'EMAIL_NOT_VERIFIED') {
      await router.replace({ path: '/verify-email', query: { email: email.value.trim() } })
    }
    // 400 GOOGLE_ACCOUNT_USE_SSO -> pesan sudah di store, sorot tombol Google.
    /* error lain sudah di store */
  }
}

async function onGoogleCredential(idToken: string) {
  googleError.value = ''
  try {
    const { useAuthStore } = await import('@/stores/authStore')
    const store = useAuthStore()
    const { needsOnboarding } = await store.loginWithGoogle(idToken)
    if (needsOnboarding) {
      await router.replace('/onboarding')
      return
    }
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : ''
    if (redirect) await router.replace(redirect)
    else await router.replace(store.roleHome())
  } catch {
    googleError.value = 'Login Google gagal. Coba lagi.'
  }
}
</script>
