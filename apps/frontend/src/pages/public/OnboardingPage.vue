<template>
  <div class="bg-cream/60">
    <div class="sv-container flex min-h-[calc(100vh-16rem)] items-center justify-center py-12">
      <Card
        class="w-full max-w-lg"
        title="Lengkapi profil Anda"
        subtitle="Satu langkah lagi sebelum masuk dashboard."
      >
        <form class="grid gap-4 sm:grid-cols-2" novalidate @submit.prevent="onSubmit">
          <div class="sm:col-span-2">
            <Alert v-if="authError" variant="error" title="Gagal menyimpan">{{ authError }}</Alert>
          </div>
          <div class="sm:col-span-2">
            <Input id="email" :model-value="email" label="Email (dari Google)" type="email" disabled />
          </div>
          <Input
            id="fullName" v-model="form.fullName" label="Nama lengkap" autocomplete="name"
            placeholder="cth. Sinta Prabowo" required :error="err('fullName')" @blur="touch('fullName')"
          />
          <Input
            id="organization" v-model="form.organization" label="Organisasi / Perusahaan"
            autocomplete="organization" placeholder="cth. PT Maju Jaya" required
            :error="err('organization')" @blur="touch('organization')"
          />
          <Input
            id="phone" v-model="form.phone" label="Nomor telepon" type="tel" autocomplete="tel"
            placeholder="cth. +628123456789" required :error="err('phone')" @blur="touch('phone')"
          />
          <div class="flex flex-col gap-1.5">
            <label for="role" class="text-sm font-medium text-slate-800">
              Peran <span class="text-[#B3261E]" aria-hidden="true">*</span>
            </label>
            <select
              id="role" v-model="form.role" required
              class="w-full rounded-md border border-light-blue bg-white px-3 py-2 focus:border-deep-blue focus:outline-none focus:ring-2 focus:ring-deep-blue/30"
            >
              <option value="ORG_ADMIN">Org Admin — upload & minta tanda tangan</option>
              <option value="SIGNER">Signer — review & tanda tangani</option>
            </select>
          </div>
          <div class="sm:col-span-2">
            <Input
              id="purpose" v-model="form.purpose" label="Keperluan penggunaan"
              placeholder="cth. TTD kontrak vendor" required :error="err('purpose')" @blur="touch('purpose')"
            />
          </div>
          <div class="sm:col-span-2">
            <Button type="submit" block :loading="isLoading" :disabled="!canSubmit">
              Simpan & masuk dashboard
            </Button>
          </div>
        </form>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { Alert, Button, Card, Input } from '@/components/ui'
import { useAuth } from '@/composables/useAuth'
import { useAuthStore } from '@/stores/authStore'
import { isPhone } from '@/utils/validators'

const router = useRouter()
const store = useAuthStore()
const { completeProfile, isLoading, error: authError } = useAuth()

const email = computed(() => store.user?.email ?? '')
const form = reactive({
  fullName: store.user?.fullName ?? '',
  organization: '',
  phone: '',
  role: 'ORG_ADMIN' as 'ORG_ADMIN' | 'SIGNER',
  purpose: '',
})
const touchedFields = reactive<Record<string, boolean>>({})

function touch(k: string) {
  touchedFields[k] = true
}

function err(k: keyof typeof form): string {
  if (!touchedFields[k]) return ''
  if (k === 'fullName') return form.fullName.trim().length >= 3 ? '' : 'Nama minimal 3 karakter.'
  if (k === 'organization') return form.organization.trim().length >= 2 ? '' : 'Organisasi wajib diisi.'
  if (k === 'phone') return isPhone(form.phone) ? '' : 'Nomor telepon tidak valid.'
  if (k === 'purpose') return form.purpose.trim().length >= 3 ? '' : 'Ceritakan keperluan penggunaan.'
  return ''
}

const canSubmit = computed(
  () =>
    form.fullName.trim().length >= 3 &&
    form.organization.trim().length >= 2 &&
    isPhone(form.phone) &&
    form.purpose.trim().length >= 3 &&
    !isLoading.value,
)

onMounted(async () => {
  // Sudah lengkap -> langsung ke dashboard per role (cegah loop onboarding).
  if (store.isAuthenticated && !store.needsOnboarding) {
    await router.replace(store.roleHome())
  }
})

async function onSubmit() {
  Object.keys(form).forEach(touch)
  if (!canSubmit.value) return
  try {
    await completeProfile({
      fullName: form.fullName.trim(),
      organization: form.organization.trim(),
      phone: form.phone.trim(),
      role: form.role,
      purpose: form.purpose.trim(),
    })
    await router.replace(store.roleHome())
  } catch {
    /* error sudah di store */
  }
}
</script>
