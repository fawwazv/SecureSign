<template>
  <section aria-label="Detail permintaan tanda tangan" class="flex flex-col gap-4">
    <Button variant="ghost" size="sm" class="self-start" @click="back">← Kembali</Button>
    <Alert v-if="error" variant="error" title="Gagal memuat">{{ error }}</Alert>
    <Alert v-if="notice" variant="success" title="Berhasil">{{ notice }}</Alert>

    <div v-if="loading" aria-busy="true"><Card><p class="text-sm text-slate-400">Memuat permintaan…</p></Card></div>

    <div v-else-if="item" class="grid gap-4 lg:grid-cols-2">
      <Card title="Review dokumen" :subtitle="`Status: ${item.status}`">
        <div class="flex flex-col gap-3 text-sm">
          <p><span class="font-semibold text-deep-blue">Dokumen:</span> {{ item.documentId }}</p>
          <p v-if="item.message" class="rounded-md bg-cream p-3 text-brown">“{{ item.message }}”</p>
          <p v-if="item.rejectReason" class="rounded-md bg-red-50 p-3 text-[#B3261E]">Alasan tolak: {{ item.rejectReason }}</p>
          <div class="flex flex-col gap-1.5">
            <label for="approve-key" class="text-sm font-medium text-slate-800">Key pair penandatangan</label>
            <select
              id="approve-key" v-model="keyPairId" required
              class="w-full rounded-md border border-light-blue bg-white px-3 py-2 focus:border-deep-blue focus:outline-none focus:ring-2 focus:ring-deep-blue/30"
            >
              <option value="" disabled>Pilih key pair…</option>
              <option v-for="k in activeKeys" :key="k.id" :value="k.id">
                {{ k.algorithm }} — {{ k.id.slice(0, 8) }}…
              </option>
            </select>
            <p v-if="!activeKeys.length" class="text-xs text-slate-500">
              Belum ada key aktif. Pilih algoritma lalu buat key baru di sini.
            </p>
            <div v-if="!activeKeys.length" class="flex flex-wrap items-end gap-2">
              <div class="flex min-w-40 flex-col gap-1.5">
                <label for="new-key-algo" class="text-xs font-medium text-slate-600">Algoritma</label>
                <select
                  id="new-key-algo" v-model="newKeyAlgo"
                  class="w-full rounded-md border border-light-blue bg-white px-3 py-2 text-sm focus:border-deep-blue focus:outline-none focus:ring-2 focus:ring-deep-blue/30"
                >
                  <option value="ED25519">Ed25519 (cepat, disarankan)</option>
                  <option value="ECDSA_P256">ECDSA P-256</option>
                  <option value="RSA_PSS_2048">RSA-2048 PSS</option>
                </select>
              </div>
              <Button variant="secondary" :loading="creatingKey" @click="createKey">
                Buat key pair
              </Button>
            </div>
            <p v-if="keyError" role="alert" class="text-xs text-[#B3261E]">{{ keyError }}</p>
          </div>
          <div class="flex flex-wrap gap-2">
            <Button variant="primary" :loading="acting" :disabled="!keyPairId.trim() || item.status !== 'PENDING'" @click="doApprove">
              Tandatangani
            </Button>
            <Button variant="danger" :disabled="item.status !== 'PENDING'" @click="rejectOpen = true">
              Tolak
            </Button>
          </div>
          <QRViewer v-if="qrPayload" :qr-payload="qrPayload" />
        </div>
      </Card>
      <PDFPreview :src="previewUrl" title="Dokumen yang diminta" />
      <p v-if="previewError" role="alert" class="text-xs text-[#B3261E]">{{ previewError }}</p>
    </div>

    <Modal :open="rejectOpen" title="Tolak dokumen" @close="rejectOpen = false">
      <form class="flex flex-col gap-4" @submit.prevent="doReject">
        <Input id="reject-reason" v-model="reason" label="Alasan penolakan" placeholder="cth. Isi kontrak belum sesuai kesepakatan" required />
        <p v-if="rejectError" role="alert" class="text-xs text-[#B3261E]">{{ rejectError }}</p>
        <div class="flex justify-end gap-2">
          <Button variant="ghost" @click="rejectOpen = false">Batal</Button>
          <Button type="submit" variant="danger" :loading="acting">Tolak dokumen</Button>
        </div>
      </form>
    </Modal>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Alert from '@/components/ui/Alert.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Input from '@/components/ui/Input.vue'
import Modal from '@/components/ui/Modal.vue'
import PDFPreview from '@/components/domain/PDFPreview.vue'
import QRViewer from '@/components/domain/QRViewer.vue'
import { documentService, downloadDocumentBlob, type KeyPairItem, type SignRequestItem } from '@/services/documentService'
import { toApiMessage } from '@/services/apiClient'
import { useSignRequest } from '@/composables/useSignRequest'

const route = useRoute()
const router = useRouter()
const { approve, reject } = useSignRequest()

const id = computed(() => String(route.params.id))
const item = ref<SignRequestItem | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const notice = ref('')
const keyPairId = ref('')
const keys = ref<KeyPairItem[]>([])
const activeKeys = computed(() => keys.value.filter((k) => !k.revoked))
const newKeyAlgo = ref<'RSA_PSS_2048' | 'ECDSA_P256' | 'ED25519'>('ED25519')
const creatingKey = ref(false)
const keyError = ref('')
const qrPayload = ref('')
const previewUrl = ref('')
const previewError = ref('')

function setPreviewUrl(url: string) {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = url
}
const rejectOpen = ref(false)
const reason = ref('')
const rejectError = ref('')
const acting = ref(false)

function back() {
  router.push('/signer')
}

async function doApprove() {
  notice.value = ''
  acting.value = true
  try {
    const sig = await approve(id.value, keyPairId.value.trim())
    qrPayload.value = sig.qrPayload
    notice.value = 'Dokumen ditandatangani. QR tertempel di dokumen final.'
    // Jangan load() ulang: request yang sudah APPROVED keluar dari daftar
    // pending dan load() akan menuduh "tidak ditemukan". Update lokal saja.
    if (item.value) item.value = { ...item.value, status: 'APPROVED' }
  } catch (e) {
    error.value = toApiMessage(e, 'Tanda tangan gagal.')
  } finally {
    acting.value = false
  }
}

async function doReject() {
  rejectError.value = ''
  if (!reason.value.trim()) {
    rejectError.value = 'Alasan penolakan wajib diisi.'
    return
  }
  acting.value = true
  try {
    const updated = await reject(id.value, reason.value.trim())
    rejectOpen.value = false
    notice.value = 'Dokumen ditolak. Org Admin akan menerima notifikasi.'
    // Sama seperti approve: tidak load() ulang agar tidak "tidak ditemukan".
    if (item.value) item.value = { ...item.value, ...updated }
  } catch (e) {
    rejectError.value = toApiMessage(e, 'Penolakan gagal.')
  } finally {
    acting.value = false
  }
}

async function load() {
  loading.value = true
  error.value = null
  previewError.value = ''
  try {
    const pending = await documentService.listPendingSignRequests({ page: 1, limit: 100 })
    item.value = pending.data.find((r) => r.id === id.value) ?? null
    if (!item.value) error.value = 'Permintaan tidak ditemukan atau sudah diproses.'
    else await Promise.all([loadPreview(item.value.documentId), loadKeys()])
  } catch (e) {
    error.value = toApiMessage(e, 'Gagal memuat permintaan.')
  } finally {
    loading.value = false
  }
}

async function loadPreview(documentId: string) {
  setPreviewUrl('')
  try {
    const blob = await downloadDocumentBlob(documentId, 'original')
    setPreviewUrl(URL.createObjectURL(blob))
  } catch (e) {
    previewError.value = toApiMessage(e, 'Pratinjau tidak dapat dimuat.')
  }
}

async function loadKeys() {
  try {
    const res = await documentService.listKeys()
    keys.value = res.data
  } catch {
    keys.value = []
  }
}

async function createKey() {
  keyError.value = ''
  creatingKey.value = true
  try {
    const key = await documentService.generateKeyPair(newKeyAlgo.value)
    await loadKeys()
    keyPairId.value = key.id
  } catch (e) {
    keyError.value = toApiMessage(e, 'Pembuatan key gagal.')
  } finally {
    creatingKey.value = false
  }
}

onBeforeUnmount(() => setPreviewUrl(''))

onMounted(load)
</script>
