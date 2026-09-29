<template>
  <section aria-label="Detail dokumen" class="flex flex-col gap-4">
    <Button variant="ghost" size="sm" class="self-start" @click="back">← Kembali</Button>
    <Alert v-if="error" variant="error" title="Gagal memuat">{{ error }}</Alert>

    <div v-if="loading" aria-busy="true"><Card><p class="text-sm text-slate-400">Memuat detail…</p></Card></div>

    <div v-else-if="doc" class="grid gap-4 lg:grid-cols-2">
      <Card :title="doc.title" :subtitle="`Status: ${doc.status}`">
        <div class="flex flex-col gap-2 text-sm">
          <p v-if="doc.description" class="text-slate-600">{{ doc.description }}</p>
          <p><span class="font-semibold text-deep-blue">Hash SHA-256:</span> <code class="break-all text-xs">{{ doc.fileHash }}</code></p>
          <p><span class="font-semibold text-deep-blue">Versi:</span> {{ doc.version }}</p>
          <p><span class="font-semibold text-deep-blue">Diperbarui:</span> {{ formatDate(doc.updatedAt) }}</p>
          <div class="mt-2 flex items-center gap-2">
            <Badge :tone="tone">{{ doc.status }}</Badge>
            <Button v-if="doc.status === 'DRAFT'" variant="primary" size="sm" @click="openRequest">
              Minta tanda tangan
            </Button>
          </div>
        </div>
      </Card>
      <QrEditor
        :key="doc.id"
        :document-id="doc.id"
        :page-count="doc.pageCount || 1"
        :initial="doc.qrPlacements || []"
        :can-edit="doc.status === 'DRAFT'"
      >
        <Alert v-if="previewWarning" variant="warning" title="File bertanda tidak ditemukan">{{ previewWarning }}</Alert>
        <PDFPreview :src="previewUrl" :title="doc.title" />
      </QrEditor>
      <p v-if="previewError" role="alert" class="text-xs text-[#B3261E]">{{ previewError }}</p>
      <div v-if="previewUrl" class="flex flex-wrap items-center gap-2">
        <span class="text-xs text-slate-500">
          Pratinjau: {{ previewKind === 'signed' ? 'PDF bertanda (ber-QR)' : 'PDF asli (tanpa QR)' }}
        </span>
        <Button size="sm" variant="secondary" :loading="downloading" @click="downloadKind('original')">
          Unduh PDF asli
        </Button>
        <Button
          v-if="doc.status === 'SIGNED'"
          size="sm" variant="secondary" :loading="downloading" @click="downloadKind('signed')"
        >
          Unduh PDF bertanda
        </Button>
      </div>
      <p v-if="downloadError" role="alert" class="text-xs text-[#B3261E]">{{ downloadError }}</p>
    </div>

    <Modal :open="reqOpen" title="Minta tanda tangan" @close="reqOpen = false">
      <form class="flex flex-col gap-4" @submit.prevent="submitRequest">
        <div class="flex flex-col gap-1.5">
          <label for="signer-id" class="text-sm font-medium text-slate-800">
            Penanda tangan <span class="text-[#B3261E]" aria-hidden="true">*</span>
          </label>
          <select
            id="signer-id" v-model="signerId" required
            class="w-full rounded-md border border-light-blue bg-white px-3 py-2 focus:border-deep-blue focus:outline-none focus:ring-2 focus:ring-deep-blue/30"
          >
            <option value="" disabled>Pilih penanda tangan…</option>
            <option v-for="s in signers" :key="s.id" :value="s.id">
              {{ s.fullName }} — {{ s.email }}
            </option>
          </select>
        </div>
        <Input id="req-msg" v-model="message" label="Pesan (opsional)" placeholder="Mohon review & tanda tangani" />
        <p v-if="reqError" role="alert" class="text-xs text-[#B3261E]">{{ reqError }}</p>
        <div class="flex justify-end gap-2">
          <Button variant="ghost" @click="reqOpen = false">Batal</Button>
          <Button type="submit" variant="primary" :loading="requesting">Kirim permintaan</Button>
        </div>
      </form>
    </Modal>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Alert from '@/components/ui/Alert.vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Input from '@/components/ui/Input.vue'
import Modal from '@/components/ui/Modal.vue'
import PDFPreview from '@/components/domain/PDFPreview.vue'
import QrEditor from '@/components/domain/QrEditor.vue'
import { documentService, downloadDocumentBlob, listUsers, type DocumentItem } from '@/services/documentService'
import { toApiMessage, toApiCodeAsync, toApiMessageAsync } from '@/services/apiClient'
import { useDocument } from '@/composables/useDocument'

const route = useRoute()
const router = useRouter()
const { requestSign } = useDocument()

const doc = ref<DocumentItem | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const reqOpen = ref(false)
const signerId = ref('')
const message = ref('')
const reqError = ref('')
const requesting = ref(false)

const id = computed(() => String(route.params.id))
const previewUrl = ref('')
const previewError = ref('')
const previewWarning = ref('')
const previewKind = ref<'signed' | 'original' | ''>('')
const downloadError = ref('')
const downloading = ref(false)
let previewSeq = 0
const signers = ref<{ id: string; fullName: string; email: string; organization: string }[]>([])
const tone = computed(() => {
  switch (doc.value?.status) {
    case 'PENDING':
      return 'pending' as const
    case 'SIGNED':
      return 'signed' as const
    case 'REJECTED':
      return 'rejected' as const
    default:
      return 'draft' as const
  }
})

function back() {
  router.push('/org')
}

function formatDate(v: string): string {
  try {
    return new Date(v).toLocaleString('id-ID', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch {
    return v
  }
}

async function submitRequest() {
  reqError.value = ''
  if (!signerId.value.trim()) {
    reqError.value = 'ID Signer wajib diisi.'
    return
  }
  requesting.value = true
  try {
    await requestSign(id.value, { signerId: signerId.value.trim(), message: message.value.trim() || undefined })
    reqOpen.value = false
    await load()
  } catch (e) {
    reqError.value = toApiMessage(e, 'Request tanda tangan gagal.')
  } finally {
    requesting.value = false
  }
}

async function load() {
  loading.value = true
  error.value = null
  previewError.value = ''
  previewWarning.value = ''
  previewKind.value = ''
  downloadError.value = ''
  try {
    doc.value = await documentService.getDocument(id.value)
    if (route.query.request === '1' && doc.value.status === 'DRAFT') await openRequest()
    await loadPreview()
  } catch (e) {
    error.value = toApiMessage(e, 'Dokumen tidak ditemukan.')
  } finally {
    loading.value = false
  }
}

/** Unduh via apiClient (bawa JWT) -> object URL untuk iframe. */
async function loadPreview() {
  const seq = ++previewSeq
  setPreviewUrl('')
  if (!doc.value) return
  const kind = doc.value.status === 'SIGNED' ? 'signed' : 'original'
  try {
    const blob = await downloadDocumentBlob(doc.value.id, kind)
    if (seq !== previewSeq) return
    setPreviewUrl(URL.createObjectURL(blob))
    previewKind.value = kind
  } catch (e) {
    if (seq !== previewSeq) return
    const code = await toApiCodeAsync(e)
    // File bertanda lama hilang: tampilkan versi asli agar dokumen tetap terbaca.
    if (kind === 'signed' && (code === 'SIGNED_FILE_NOT_FOUND' || code === 'NOT_SIGNED_YET')) {
      try {
        const fallback = await downloadDocumentBlob(doc.value.id, 'original')
        if (seq !== previewSeq) return
        setPreviewUrl(URL.createObjectURL(fallback))
        previewKind.value = 'original'
        previewWarning.value = await toApiMessageAsync(e, 'File bertanda tidak ditemukan, menampilkan versi asli.')
        return
      } catch (e2) {
        previewError.value = await toApiMessageAsync(e2, 'Pratinjau tidak dapat dimuat.')
        return
      }
    }
    previewError.value = await toApiMessageAsync(e, 'Pratinjau tidak dapat dimuat.')
  }
}

function setPreviewUrl(url: string) {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = url
}

/** Unduh eksplisit per versi agar file untuk verifikasi tidak tertukar. */
async function downloadKind(kind: 'original' | 'signed') {
  if (!doc.value || downloading.value) return
  downloadError.value = ''
  downloading.value = true
  try {
    const blob = await downloadDocumentBlob(doc.value.id, kind)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${doc.value.title.replace(/[^\w\-]+/g, '_').slice(0, 80)}-${kind}.pdf`
    document.body.appendChild(a)
    a.click()
    a.remove()
    setTimeout(() => URL.revokeObjectURL(url), 10_000)
  } catch (e) {
    downloadError.value = await toApiMessageAsync(
      e,
      kind === 'signed'
        ? 'PDF bertanda tidak dapat diunduh (file bertanda hilang di penyimpanan).'
        : 'PDF asli tidak dapat diunduh.',
    )
  } finally {
    downloading.value = false
  }
}

/** Muat daftar Signer saat modal dibuka (bukan UUID mentah). */
async function openRequest() {
  reqError.value = ''
  reqOpen.value = true
  if (signers.value.length) return
  try {
    const res = await listUsers({ role: 'SIGNER', limit: 100 })
    signers.value = res.data
  } catch (e) {
    reqError.value = toApiMessage(e, 'Daftar penanda tangan gagal dimuat.')
  }
}

onBeforeUnmount(() => setPreviewUrl(''))

onMounted(load)
</script>
