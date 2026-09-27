<template>
  <div class="bg-white">
    <div class="sv-container sv-section max-w-3xl">
      <h1 class="text-deep-blue">Verifikasi dokumen publik</h1>
      <p class="mt-2 text-slate-600">
        Tanpa login. Upload PDF bertanda tangan atau masukkan token dari QR untuk memeriksa
        hash &amp; signature (F-13 / F-14).
      </p>

      <Tabs v-model="mode" :tabs="tabs" label="Metode verifikasi" class="mt-6" />

      <div v-if="mode === 'upload'" class="sv-card mt-4 p-6">
        <label for="pdf" class="text-sm font-medium">File PDF (maks 25 MB)</label>
        <input
          id="pdf" type="file" accept="application/pdf"
          class="mt-2 block w-full rounded-md border border-light-blue bg-white p-2 text-sm"
          @change="onFile"
        />
        <p v-if="fileName" class="mt-2 text-sm text-slate-600">Dipilih: {{ fileName }}</p>
        <Button class="mt-4" :loading="loading" :disabled="!file || loading" @click="verifyFile">
          Verifikasi PDF
        </Button>
      </div>

      <div v-else class="sv-card mt-4 p-6">
        <Input
          id="token" v-model="token" label="Token / tautan QR"
          placeholder="cth. sv_9f2c… atau tempel URL verifikasi" :error="tokenTouched && !token ? 'Token wajib diisi.' : ''"
          @blur="tokenTouched = true"
        />
        <Button class="mt-4" :loading="loading" :disabled="!token || loading" @click="verifyToken">
          Verifikasi token
        </Button>
      </div>

      <Alert v-if="error" variant="error" title="Verifikasi gagal" class="mt-4">{{ error }}</Alert>

      <Card v-if="result" class="mt-4" title="Hasil verifikasi">
        <div class="flex items-center gap-3">
          <Badge :tone="result.status === 'VALID' ? 'signed' : 'rejected'">
            {{ result.status === 'VALID' ? 'VALID' : 'TIDAK VALID' }}
          </Badge>
          <p class="text-sm text-slate-600">{{ result.reason ?? defaultReason }}</p>
        </div>
        <dl class="mt-4 grid gap-2 text-sm sm:grid-cols-2">
          <div><dt class="text-slate-500">Dokumen</dt><dd class="font-medium">{{ result.documentName ?? '-' }}</dd></div>
          <div><dt class="text-slate-500">Penandatangan</dt><dd class="font-medium">{{ result.signerName ?? '-' }}</dd></div>
          <div><dt class="text-slate-500">Waktu tanda tangan</dt><dd class="font-medium">{{ result.signedAt ? formatDate(result.signedAt) : '-' }}</dd></div>
        </dl>
        <div v-if="result.auditTrail?.length" class="mt-4">
          <p class="font-semibold">Audit trail singkat</p>
          <Table
            class="mt-2" :columns="auditCols"
            :rows="result.auditTrail.map((a) => ({ event: a.event, at: formatDate(a.at), actor: a.actor ?? '-' }))"
          />
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Alert, Badge, Button, Card, Input, Table, Tabs } from '@/components/ui'
import { verifyService } from '@/services/authService'
import { toApiMessage } from '@/services/apiClient'
import { formatDate } from '@/utils/formatDate'
import type { VerifyResult } from '@/types/api'

const tabs = [
  { value: 'upload', label: 'Upload PDF' },
  { value: 'token', label: 'Token / QR' },
]
const mode = ref('upload')
const file = ref<File | null>(null)
const token = ref('')
const tokenTouched = ref(false)
const loading = ref(false)
const error = ref('')
const result = ref<VerifyResult | null>(null)

const fileName = computed(() => file.value?.name ?? '')
const defaultReason = computed(() =>
  result.value?.status === 'VALID' ? 'Hash & signature cocok.' : 'Hash / signature / kunci / QR tidak valid.',
)
const auditCols = [
  { key: 'event', label: 'Peristiwa' },
  { key: 'at', label: 'Waktu' },
  { key: 'actor', label: 'Aktor' },
]

function onFile(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0] ?? null
  if (f && f.size > 25 * 1024 * 1024) {
    error.value = 'Ukuran file melebihi 25 MB.'
    file.value = null
    return
  }
  error.value = ''
  result.value = null
  file.value = f
}

async function verifyFile() {
  if (!file.value) return
  loading.value = true
  error.value = ''
  try {
    result.value = await verifyService.verifyPublic(file.value)
  } catch (e) {
    // F-14: dokumen ditolak bila hash/signature/kunci/QR tidak valid.
    error.value = toApiMessage(e, 'Dokumen TIDAK VALID atau gagal diverifikasi.')
    result.value = null
  } finally {
    loading.value = false
  }
}

async function verifyToken() {
  tokenTouched.value = true
  if (!token.value) return
  loading.value = true
  error.value = ''
  try {
    result.value = await verifyService.verifyByToken(token.value.trim())
  } catch (e) {
    error.value = toApiMessage(e, 'Token TIDAK VALID atau gagal diverifikasi.')
    result.value = null
  } finally {
    loading.value = false
  }
}
</script>
