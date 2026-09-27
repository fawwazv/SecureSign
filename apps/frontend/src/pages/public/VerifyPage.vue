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

      <div v-else-if="mode === 'token'" class="sv-card mt-4 p-6">
        <Input
          id="token" v-model="token" label="Token / tautan QR"
          placeholder="cth. sv_9f2c… atau tempel URL verifikasi" :error="tokenTouched && !token ? 'Token wajib diisi.' : ''"
          @blur="tokenTouched = true"
        />
        <Button class="mt-4" :loading="loading" :disabled="!token || loading" @click="verifyToken">
          Verifikasi token
        </Button>
      </div>

      <div v-else class="sv-card mt-4 p-6">
        <p class="text-sm text-slate-600">
          Arahkan kamera ke QR pada dokumen. Hasil pindaian otomatis diverifikasi.
        </p>
        <Alert v-if="!qrSupported" variant="warning" title="Kamera tidak tersedia" class="mt-3">
          Akses kamera membutuhkan koneksi aman (HTTPS atau localhost) dan izin browser.
          Gunakan tab Upload PDF atau Token, atau buka situs via HTTPS.
        </Alert>
        <div v-else class="mt-3 overflow-hidden rounded-md border border-light-blue bg-black">
          <div id="sv-qr-reader" class="w-full" />
        </div>
        <p v-if="scanStatus" class="mt-2 text-sm text-slate-600" role="status">{{ scanStatus }}</p>
        <div v-if="qrSupported" class="mt-4 flex flex-wrap gap-2">
          <Button v-if="!scanning" :disabled="loading" @click="startScan">Mulai kamera</Button>
          <Button v-else variant="secondary" @click="stopScan">Hentikan</Button>
        </div>
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
import { computed, onBeforeUnmount, ref } from 'vue'
import { Html5Qrcode } from 'html5-qrcode'
import { Alert, Badge, Button, Card, Input, Table, Tabs } from '@/components/ui'
import { verifyService } from '@/services/authService'
import { toApiMessage } from '@/services/apiClient'
import { formatDate } from '@/utils/formatDate'
import { extractTokenFromQrText, isCameraQrSupported } from '@/utils/qr'
import type { VerifyResult } from '@/types/api'

const tabs = [
  { value: 'upload', label: 'Upload PDF' },
  { value: 'token', label: 'Token / QR' },
  { value: 'scan', label: 'Scan QR' },
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

// --- Scan QR via kamera (html5-qrcode: lintas browser — Chrome, Edge, Firefox, Safari) ---
const scanning = ref(false)
const scanStatus = ref('')
const qrSupported = ref(isCameraQrSupported())
let scanner: Html5Qrcode | null = null

async function startScan() {
  error.value = ''
  result.value = null
  scanStatus.value = ''
  if (!qrSupported.value || !navigator.mediaDevices?.getUserMedia) {
    qrSupported.value = false
    scanStatus.value = 'Kamera tidak tersedia di perangkat/browser ini.'
    return
  }
  try {
    stopScannerInstance()
    scanStatus.value = 'Meminta akses kamera…'
    scanner = new Html5Qrcode('sv-qr-reader')
    scanning.value = true
    await scanner.start(
      { facingMode: 'environment' },
      { fps: 10, qrbox: { width: 250, height: 250 } },
      async (decodedText: string) => {
        const found = extractTokenFromQrText(decodedText)
        scanStatus.value = `QR terbaca: ${found}`
        await stopScan()
        token.value = found
        await verifyToken()
      },
      () => {
        /* frame tanpa QR — abaikan, lanjutkan memindai */
      },
    )
    scanStatus.value = 'Arahkan kamera ke QR…'
  } catch {
    scanStatus.value = 'Akses kamera ditolak atau tidak tersedia. Periksa izin browser.'
    await stopScan()
  }
}

function stopScannerInstance() {
  if (scanner) {
    const s = scanner
    scanner = null
    s.stop().catch(() => {})
    s.clear()
  }
}

async function stopScan() {
  stopScannerInstance()
  scanning.value = false
}

onBeforeUnmount(() => {
  stopScannerInstance()
})
</script>
