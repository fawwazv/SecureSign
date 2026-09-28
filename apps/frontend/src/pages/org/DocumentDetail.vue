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
            <Button v-if="doc.status === 'DRAFT'" variant="primary" size="sm" @click="reqOpen = true">
              Minta tanda tangan
            </Button>
          </div>
        </div>
      </Card>
      <PDFPreview :src="previewUrl" :title="doc.title" />
    </div>

    <Modal :open="reqOpen" title="Minta tanda tangan" @close="reqOpen = false">
      <form class="flex flex-col gap-4" @submit.prevent="submitRequest">
        <Input id="signer-id" v-model="signerId" label="ID Signer" placeholder="UUID user Signer" required hint="Dapatkan dari daftar user organisasi Anda" />
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
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Alert from '@/components/ui/Alert.vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Input from '@/components/ui/Input.vue'
import Modal from '@/components/ui/Modal.vue'
import PDFPreview from '@/components/domain/PDFPreview.vue'
import { documentService, previewUrlFor, type DocumentItem } from '@/services/documentService'
import { toApiMessage } from '@/services/apiClient'
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
const previewUrl = computed(() => previewUrlFor(id.value))

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
  try {
    doc.value = await documentService.getDocument(id.value)
    if (route.query.request === '1' && doc.value.status === 'DRAFT') reqOpen.value = true
  } catch (e) {
    error.value = toApiMessage(e, 'Dokumen tidak ditemukan.')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
