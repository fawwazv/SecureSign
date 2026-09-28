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
          <Input id="approve-key" v-model="keyPairId" label="ID Key Pair" placeholder="UUID key pair Anda" required />
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
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Alert from '@/components/ui/Alert.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Input from '@/components/ui/Input.vue'
import Modal from '@/components/ui/Modal.vue'
import PDFPreview from '@/components/domain/PDFPreview.vue'
import QRViewer from '@/components/domain/QRViewer.vue'
import { documentService, previewUrlFor, type SignRequestItem } from '@/services/documentService'
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
const qrPayload = ref('')
const rejectOpen = ref(false)
const reason = ref('')
const rejectError = ref('')
const acting = ref(false)
const previewUrl = computed(() => (item.value?.documentId ? previewUrlFor(item.value.documentId) : ''))

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
    await load()
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
    await reject(id.value, reason.value.trim())
    rejectOpen.value = false
    notice.value = 'Dokumen ditolak. Org Admin akan menerima notifikasi.'
    await load()
  } catch (e) {
    rejectError.value = toApiMessage(e, 'Penolakan gagal.')
  } finally {
    acting.value = false
  }
}

async function load() {
  loading.value = true
  error.value = null
  try {
    const pending = await documentService.listPendingSignRequests({ page: 1, limit: 100 })
    item.value = pending.data.find((r) => r.id === id.value) ?? null
    if (!item.value) error.value = 'Permintaan tidak ditemukan atau sudah diproses.'
  } catch (e) {
    error.value = toApiMessage(e, 'Gagal memuat permintaan.')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
