<template>
  <section aria-label="Upload PDF" class="mx-auto flex max-w-2xl flex-col gap-4">
    <div>
      <h2 class="text-deep-blue">Upload Dokumen PDF</h2>
      <p class="text-sm text-slate-500">Maksimal 25 MB. Hash SHA-256 dihitung backend saat upload.</p>
    </div>

    <Alert v-if="error" variant="error" title="Upload gagal">{{ error }}</Alert>
    <Alert v-if="success" variant="success" title="Berhasil">Dokumen terupload.</Alert>

    <Card>
      <form class="flex flex-col gap-4" @submit.prevent="submit">
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
        <Input id="doc-title" v-model="title" label="Perihal / Judul" placeholder="cth. Surat Keterangan Aktif Kuliah" required :error="err('title')" @blur="touch('title')" />
        <div class="grid gap-4 sm:grid-cols-2">
          <Input id="doc-nama" v-model="nama" label="Nama mahasiswa" placeholder="cth. Muhammad Fawwazul Haq" :error="err('nama')" @blur="touch('nama')" />
          <Input id="doc-nim" v-model="nim" label="NIM" placeholder="cth. 247006111088" :error="err('nim')" @blur="touch('nim')" />
        </div>
        <div class="grid gap-4 sm:grid-cols-2">
          <div class="flex flex-col gap-1.5">
            <label for="doc-tanggal" class="text-sm font-medium text-slate-800">Tanggal surat</label>
            <input
              id="doc-tanggal" v-model="tanggal" type="date"
              class="w-full rounded-md border border-light-blue bg-white px-3 py-2 focus:border-deep-blue focus:outline-none focus:ring-2 focus:ring-deep-blue/30"
              @blur="touch('tanggal')"
            />
            <p v-if="err('tanggal')" role="alert" class="text-xs text-[#B3261E]">{{ err('tanggal') }}</p>
          </div>
          <div class="flex flex-col gap-1.5">
            <label for="doc-jenis" class="text-sm font-medium text-slate-800">Jenis dokumen</label>
            <select
              id="doc-jenis" v-model="jenis"
              class="w-full rounded-md border border-light-blue bg-white px-3 py-2 focus:border-deep-blue focus:outline-none focus:ring-2 focus:ring-deep-blue/30"
            >
              <option v-for="j in JENIS_LIST" :key="j" :value="j">{{ j }}</option>
            </select>
          </div>
        </div>
        <Input id="doc-desc" v-model="description" label="Keterangan (opsional)" placeholder="Catatan tambahan dokumen" />
        <Button type="submit" variant="primary" :loading="isLoading" :disabled="!canSubmit">
          Upload dokumen
        </Button>
      </form>
    </Card>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import Alert from '@/components/ui/Alert.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Input from '@/components/ui/Input.vue'
import { useDocument } from '@/composables/useDocument'

const JENIS_LIST = [
  'Lainnya',
  'Surat Keterangan Aktif Kuliah',
  'Surat Keterangan Lulus',
  'Surat Tugas Akhir',
  'Surat Kerja Praktik / Magang',
  'Surat Rekomendasi Beasiswa',
  'Surat Pengantar Penelitian',
  'Surat Izin Observasi / Penelitian',
  'Surat Keterangan Cuti Akademik',
  'Surat Permohonan Transkrip / Legalisir',
  'Surat Keterangan Bebas Administrasi',
] as const

const { isLoading, error, uploadDocument, clearError } = useDocument()
const router = useRouter()

const fileRef = ref<HTMLInputElement | null>(null)
const file = ref<File | null>(null)
const fileError = ref('')
const title = ref('')
const nama = ref('')
const nim = ref('')
const tanggal = ref('')
const jenis = ref<(typeof JENIS_LIST)[number]>('Lainnya')
const description = ref('')
const success = ref(false)
const touchedFields = reactive<Record<string, boolean>>({})

function touch(k: string) {
  touchedFields[k] = true
}

function err(k: 'title' | 'nama' | 'nim' | 'tanggal'): string {
  if (!touchedFields[k]) return ''
  if (k === 'title') return title.value.trim().length > 0 ? '' : 'Perihal wajib diisi.'
  if (k === 'nama') {
    if (!nama.value.trim()) return ''
    return nama.value.trim().length <= 100 ? '' : 'Nama maksimal 100 karakter.'
  }
  if (k === 'nim') {
    if (!nim.value.trim()) return ''
    return /^\d{8,20}$/.test(nim.value.trim()) ? '' : 'NIM harus digit 8-20 karakter.'
  }
  if (k === 'tanggal') {
    if (!tanggal.value) return ''
    return Number.isNaN(Date.parse(tanggal.value)) ? 'Tanggal tidak valid.' : ''
  }
  return ''
}

const metaObject = computed(() => {
  const obj: Record<string, string> = {}
  if (nama.value.trim()) obj.nama = nama.value.trim()
  if (/^\d{8,20}$/.test(nim.value.trim())) obj.nim = nim.value.trim()
  if (tanggal.value && !Number.isNaN(Date.parse(tanggal.value))) obj.tanggal = tanggal.value
  if (jenis.value && jenis.value !== 'Lainnya') obj.jenis = jenis.value
  return obj
})

const canSubmit = computed(
  () =>
    !!file.value &&
    !fileError.value &&
    title.value.trim().length > 0 &&
    (!nama.value.trim() || nama.value.trim().length <= 100) &&
    (!nim.value.trim() || /^\d{8,20}$/.test(nim.value.trim())) &&
    (!tanggal.value || !Number.isNaN(Date.parse(tanggal.value))) &&
    !isLoading.value,
)

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

async function submit() {
  Object.assign(touchedFields, { title: true, nama: true, nim: true, tanggal: true })
  if (!canSubmit.value) return
  success.value = false
  if (!file.value) return
  try {
    const meta = JSON.stringify(metaObject.value)
    const doc = await uploadDocument({
      file: file.value,
      title: title.value.trim(),
      description: description.value.trim() || undefined,
      metadata: Object.keys(metaObject.value).length ? meta : undefined,
    })
    success.value = true
    router.push(`/org/documents/${doc.id}`)
  } catch {
    /* error sudah di store */
  }
}
</script>
