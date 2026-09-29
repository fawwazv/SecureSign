<template>
  <section aria-label="Upload PDF" class="mx-auto flex max-w-2xl flex-col gap-4">
    <div>
      <h2 class="text-deep-blue">Upload Dokumen PDF</h2>
      <p class="text-sm text-slate-500">Maksimal 25 MB. Hash SHA-256 dihitung backend saat upload.</p>
    </div>

    <Alert v-if="error" variant="error" title="Upload gagal">{{ error }}</Alert>
    <Alert v-if="success" variant="success" title="Berhasil">Dokumen terupload. Lanjut isi metadata bila perlu.</Alert>

    <Card>
      <form class="flex flex-col gap-4" @submit.prevent="openMetadata">
        <div class="flex flex-col gap-1.5">
          <label for="pdf-file" class="text-sm font-medium text-slate-800">File PDF <span class="text-[#B3261E]" aria-hidden="true">*</span></label>
          <input
            id="pdf-file"
            ref="fileRef"
            type="file"
            accept="application/pdf,.pdf"
            required
            aria-describedby="pdf-hint"
            class="w-full rounded-md border border-light-blue bg-white px-3 py-2 text-base focus:border-deep-blue focus:outline-none focus:ring-2 focus:ring-deep-blue/30"
            @change="onFile"
          />
          <p id="pdf-hint" class="text-xs text-slate-500">Hanya PDF, maksimal 25 MB.</p>
          <p v-if="fileError" role="alert" class="text-xs text-[#B3261E]">{{ fileError }}</p>
        </div>
        <Input id="doc-title" v-model="title" label="Judul dokumen" placeholder="cth. Kontrak Kerja Sama 2026" required />
        <Input id="doc-desc" v-model="description" label="Deskripsi (opsional)" placeholder="Ringkasan singkat dokumen" />
        <Button type="submit" variant="primary" :loading="isLoading" :disabled="!canContinue">
          Lanjut ke metadata
        </Button>
      </form>
    </Card>

    <Modal :open="metaOpen" title="Metadata dokumen" @close="metaOpen = false">
      <div class="flex flex-col gap-4">
        <p class="text-xs text-slate-500">
          Isi pasangan nama–nilai di bawah (ikut ditandatangani). Kosongkan bila tidak perlu.
        </p>
        <div v-for="(row, i) in metaRows" :key="row.id" class="flex items-start gap-2">
          <Input :id="`meta-key-${i}`" v-model="row.key" label="Nama field" placeholder="cth. departemen" />
          <Input :id="`meta-val-${i}`" v-model="row.value" label="Nilai" placeholder="cth. Legal" />
          <Button variant="ghost" class="mt-6 shrink-0" aria-label="Hapus baris" @click="removeMetaRow(i)">
            ✕
          </Button>
        </div>
        <div>
          <Button variant="secondary" @click="addMetaRow">+ Tambah field</Button>
        </div>
        <p v-if="metaPreview" class="rounded-md bg-slate-50 p-2 font-mono text-xs text-slate-600">
          {{ metaPreview }}
        </p>
        <p v-if="metaError" role="alert" class="text-xs text-[#B3261E]">{{ metaError }}</p>
        <div class="flex justify-end gap-2">
          <Button variant="ghost" @click="metaOpen = false">Batal</Button>
          <Button variant="primary" :loading="isLoading" @click="submit">Upload dokumen</Button>
        </div>
      </div>
    </Modal>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import Alert from '@/components/ui/Alert.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Input from '@/components/ui/Input.vue'
import Modal from '@/components/ui/Modal.vue'
import { useDocument } from '@/composables/useDocument'

const { isLoading, error, uploadDocument, clearError } = useDocument()
const router = useRouter()

const fileRef = ref<HTMLInputElement | null>(null)
const file = ref<File | null>(null)
const fileError = ref('')
const title = ref('')
const description = ref('')
const metaRows = reactive<{ id: number; key: string; value: string }[]>([])
let metaSeq = 0
const metaError = ref('')
const metaOpen = ref(false)
const success = ref(false)

const metaObject = computed(() => {
  const obj: Record<string, string> = {}
  for (const row of metaRows) {
    const k = row.key.trim()
    if (k) obj[k] = row.value
  }
  return obj
})

const metaPreview = computed(() => {
  const keys = Object.keys(metaObject.value)
  return keys.length ? JSON.stringify(metaObject.value) : ''
})

function addMetaRow() {
  metaRows.push({ id: ++metaSeq, key: '', value: '' })
}

function removeMetaRow(i: number) {
  metaRows.splice(i, 1)
}

const canContinue = computed(() => !!file.value && title.value.trim().length > 0 && !fileError.value)

function onFile() {
  fileError.value = ''
  clearError()
  const f = fileRef.value?.files?.[0]
  if (!f) {
    file.value = null
    return
  }
  if (f.type !== 'application/pdf' && !f.name.toLowerCase().endsWith('.pdf')) {
    fileError.value = 'File harus berformat PDF.'
    file.value = null
    return
  }
  if (f.size > 25 * 1024 * 1024) {
    fileError.value = 'Ukuran PDF melebihi 25 MB.'
    file.value = null
    return
  }
  file.value = f
}

function openMetadata() {
  if (!canContinue.value) return
  metaError.value = ''
  metaOpen.value = true
}

async function submit() {
  metaError.value = ''
  success.value = false
  const keys = metaRows.map((r) => r.key.trim()).filter(Boolean)
  if (new Set(keys).size !== keys.length) {
    metaError.value = 'Nama field tidak boleh ganda.'
    return
  }
  if (!file.value) return
  try {
    const doc = await uploadDocument({
      file: file.value,
      title: title.value.trim(),
      description: description.value.trim() || undefined,
      metadata: metaPreview.value || undefined,
    })
    metaOpen.value = false
    success.value = true
    router.push(`/org/documents/${doc.id}`)
  } catch {
    metaOpen.value = false
  }
}
</script>
