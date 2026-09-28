<template>
  <div class="bg-cream/60">
    <div class="sv-container flex min-h-[calc(100vh-16rem)] items-center justify-center py-12">
      <Card
        class="w-full max-w-lg"
        title="Buat akun SignVault"
        subtitle="Verifikasi email + CAPTCHA sebelum login (F-02)."
      >
        <form class="grid gap-4 sm:grid-cols-2" novalidate @submit.prevent="onSubmit">
          <div class="sm:col-span-2">
            <Alert v-if="authError" variant="error" title="Registrasi gagal">{{ authError }}</Alert>
          </div>
          <Input
            id="fullName" v-model="form.fullName" label="Nama lengkap" autocomplete="name"
            placeholder="cth. Sinta Prabowo" required :error="err('fullName')" @blur="touch('fullName')"
          />
          <Input
            id="email" v-model="form.email" label="Email" type="email" autocomplete="email"
            placeholder="nama@perusahaan.id" required :error="err('email')" @blur="touch('email')"
          />
          <Input
            id="password" v-model="form.password" label="Kata sandi" type="password"
            autocomplete="new-password" placeholder="Min. 8 karakter, huruf + angka" required
            hint="Disimpan sebagai hash Argon2id di server." :error="err('password')" @blur="touch('password')"
          />
          <Input
            id="organization" v-model="form.organization" label="Organisasi / Perusahaan"
            autocomplete="organization" placeholder="cth. PT Maju Jaya" required
            :error="err('organization')" @blur="touch('organization')"
          />
          <div class="flex flex-col gap-1.5">
            <label for="role" class="text-sm font-medium text-slate-800">
              Peran <span class="text-[#B3261E]" aria-hidden="true">*</span>
            </label>
            <select
              id="role" v-model="form.role" required
              class="w-full rounded-md border border-light-blue bg-white px-3 py-2 focus:border-deep-blue focus:outline-none focus:ring-2 focus:ring-deep-blue/30"
              :aria-invalid="!!err('role')"
            >
              <option value="ORG_ADMIN">Org Admin — upload & minta tanda tangan</option>
              <option value="SIGNER">Signer — review & tanda tangani</option>
            </select>
            <p v-if="err('role')" role="alert" class="text-xs text-[#B3261E]">{{ err('role') }}</p>
          </div>
          <Input
            id="purpose" v-model="form.purpose" label="Keperluan penggunaan" placeholder="cth. TTD kontrak vendor"
            required :error="err('purpose')" @blur="touch('purpose')"
          />
          <Input
            id="phone" v-model="form.phone" label="Nomor telepon" type="tel" autocomplete="tel"
            placeholder="cth. +628123456789" required :error="err('phone')" @blur="touch('phone')"
          />
          <div class="sm:col-span-2">
            <TurnstileWidget
              ref="turnstileRef"
              @verified="onCaptchaVerified"
              @expired="onCaptchaExpired"
            />
          </div>
          <div class="sm:col-span-2">
            <Button type="submit" block :loading="isLoading" :disabled="!canSubmit">
              Daftar & kirim email verifikasi
            </Button>
            <div class="my-4 flex items-center gap-3 text-xs text-slate-500" aria-hidden="true">
              <span class="h-px flex-1 bg-slate-200"></span>
              <span>atau</span>
              <span class="h-px flex-1 bg-slate-200"></span>
            </div>
            <Alert v-if="googleError" variant="error" title="Login Google gagal">{{ googleError }}</Alert>
            <GoogleSignInButton text="signup_with" @credential="onGoogleCredential" />
            <p class="mt-3 text-center text-sm text-slate-600">
              Sudah punya akun?
              <RouterLink to="/login" class="font-semibold text-deep-blue hover:underline">Masuk</RouterLink>
            </p>
          </div>
        </form>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Alert, Button, Card, Input } from '@/components/ui'
import GoogleSignInButton from '@/components/auth/GoogleSignInButton.vue'
import TurnstileWidget from '@/components/auth/TurnstileWidget.vue'
import { useAuth } from '@/composables/useAuth'
import { useAuthStore } from '@/stores/authStore'
import { toApiCode } from '@/services/apiClient'
import { isEmail, isPhone, isStrongPassword } from '@/utils/validators'

const router = useRouter()
const { register, isLoading, error: authError } = useAuth()
const store = useAuthStore()

const form = reactive({
  fullName: '',
  email: '',
  password: '',
  organization: '',
  phone: '',
  role: 'ORG_ADMIN' as 'ORG_ADMIN' | 'SIGNER',
  purpose: '',
  captchaToken: '',
})
const captchaKey = computed(() => import.meta.env.VITE_CAPTCHA_SITE_KEY ?? '')
const turnstileRef = ref<InstanceType<typeof TurnstileWidget> | null>(null)
const googleError = ref('')
const touchedFields = reactive<Record<string, boolean>>({})

function touch(k: string) {
  touchedFields[k] = true
}

function err(k: keyof typeof form): string {
  if (!touchedFields[k]) return ''
  switch (k) {
    case 'fullName':
      return form.fullName.trim().length >= 3 ? '' : 'Nama minimal 3 karakter.'
    case 'email':
      return isEmail(form.email) ? '' : 'Format email tidak valid.'
    case 'password':
      return isStrongPassword(form.password) ? '' : 'Min. 8 karakter, mengandung huruf + angka.'
    case 'organization':
      return form.organization.trim().length >= 2 ? '' : 'Organisasi wajib diisi.'
    case 'phone':
      return isPhone(form.phone) ? '' : 'Nomor telepon tidak valid (cth. +62812...).'
    case 'role':
      return ['ORG_ADMIN', 'SIGNER'].includes(form.role) ? '' : 'Pilih peran.'
    case 'purpose':
      return form.purpose.trim().length >= 3 ? '' : 'Ceritakan keperluan penggunaan.'
    default:
      return ''
  }
}

const canSubmit = computed(
  () =>
    form.fullName.trim().length >= 3 &&
    isEmail(form.email) &&
    isStrongPassword(form.password) &&
    form.organization.trim().length >= 2 &&
    isPhone(form.phone) &&
    form.purpose.trim().length >= 3 &&
    (form.captchaToken.length > 0 || captchaKey.value.length === 0) &&
    !isLoading.value,
)

function onCaptchaVerified(token: string) {
  form.captchaToken = token
}

function onCaptchaExpired() {
  form.captchaToken = ''
}

async function onGoogleCredential(idToken: string) {
  googleError.value = ''
  try {
    const { needsOnboarding } = await store.loginWithGoogle(idToken)
    if (needsOnboarding) await router.replace('/onboarding')
    else await router.replace(store.roleHome())
  } catch (e) {
    googleError.value = toApiCode(e) ? 'Login Google gagal. Coba lagi.' : 'Login Google gagal. Coba lagi.'
  }
}

async function onSubmit() {
  Object.keys(form).forEach(touch)
  if (!canSubmit.value) return
  try {
    await register({
      fullName: form.fullName.trim(),
      email: form.email.trim(),
      password: form.password,
      organization: form.organization.trim(),
      phone: form.phone.trim(),
      role: form.role,
      purpose: form.purpose.trim(),
      captchaToken: form.captchaToken || undefined,
    })
    await router.replace({ path: '/verify-email', query: { email: form.email.trim(), sent: '1' } })
  } catch (e) {
    // CAPTCHA gagal -> reset widget agar token baru bisa diminta.
    if (toApiCode(e) === 'CAPTCHA_FAILED') {
      form.captchaToken = ''
      turnstileRef.value?.reset()
    }
    /* error lain sudah di store */
  }
}
</script>
