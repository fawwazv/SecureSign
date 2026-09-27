<template>
  <div class="bg-cream/60">
    <div class="sv-container flex min-h-[calc(100vh-16rem)] items-center justify-center py-12">
      <Card
        class="w-full max-w-lg"
        title="Buat akun SignVault"
        subtitle="6 field • verifikasi email sebelum login (F-02)."
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
          <div class="sm:col-span-2">
            <Button type="submit" block :loading="isLoading" :disabled="!canSubmit">
              Daftar & kirim email verifikasi
            </Button>
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
import { computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { Alert, Button, Card, Input } from '@/components/ui'
import { useAuth } from '@/composables/useAuth'
import { isEmail, isStrongPassword } from '@/utils/validators'

const router = useRouter()
const { register, isLoading, error: authError } = useAuth()

const form = reactive({
  fullName: '',
  email: '',
  password: '',
  organization: '',
  role: 'ORG_ADMIN' as 'ORG_ADMIN' | 'SIGNER',
  purpose: '',
})
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
    form.purpose.trim().length >= 3 &&
    !isLoading.value,
)

async function onSubmit() {
  Object.keys(form).forEach(touch)
  if (!canSubmit.value) return
  try {
    await register({
      fullName: form.fullName.trim(),
      email: form.email.trim(),
      password: form.password,
      organization: form.organization.trim(),
      role: form.role,
      purpose: form.purpose.trim(),
    })
    await router.replace({ path: '/verify-email', query: { email: form.email.trim(), sent: '1' } })
  } catch {
    /* error di store */
  }
}
</script>
