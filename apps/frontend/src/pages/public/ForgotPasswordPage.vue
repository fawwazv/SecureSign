<template>
  <div class="bg-cream/60">
    <div class="sv-container flex min-h-[calc(100vh-16rem)] items-center justify-center py-12">
      <Card class="w-full max-w-md" title="Lupa kata sandi" subtitle="Kami kirim tautan reset ke email Anda.">
        <form class="space-y-4" novalidate @submit.prevent="onSubmit">
          <Alert v-if="sent" variant="success" title="Tautan terkirim">
            Jika email terdaftar, tautan reset sudah dikirim. Cek kotak masuk &amp; spam.
          </Alert>
          <Alert v-else-if="error" variant="error" title="Gagal">{{ error }}</Alert>
          <Input
            id="email" v-model="email" label="Email" type="email" autocomplete="email"
            placeholder="nama@perusahaan.id" required :error="emailError" @blur="touched = true"
          />
          <Button type="submit" block :loading="loading" :disabled="!canSubmit">
            Kirim tautan reset
          </Button>
          <p class="text-center text-sm">
            <RouterLink to="/login" class="text-deep-blue hover:underline">Kembali masuk</RouterLink>
          </p>
        </form>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Alert, Button, Card, Input } from '@/components/ui'
import { authService } from '@/services/authService'
import { toApiMessage } from '@/services/apiClient'
import { isEmail } from '@/utils/validators'

const email = ref('')
const touched = ref(false)
const loading = ref(false)
const sent = ref(false)
const error = ref('')

const emailError = computed(() => {
  if (!touched.value || email.value === '') return ''
  return isEmail(email.value) ? '' : 'Format email tidak valid.'
})
const canSubmit = computed(() => isEmail(email.value) && !loading.value)

async function onSubmit() {
  touched.value = true
  if (!canSubmit.value) return
  loading.value = true
  error.value = ''
  try {
    await authService.forgotPassword(email.value.trim())
    sent.value = true
  } catch (e) {
    error.value = toApiMessage(e, 'Gagal mengirim tautan reset.')
  } finally {
    loading.value = false
  }
}
</script>
