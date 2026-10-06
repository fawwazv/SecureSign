<template>
  <section aria-label="Batch signing" class="mx-auto flex max-w-3xl flex-col gap-4">
    <div>
      <h2 class="text-deep-blue">Batch Signing</h2>
      <p class="text-sm text-slate-500">Tandatangani banyak dokumen dalam sekali aksi — hasil dihitung per dokumen.</p>
    </div>

    <Alert v-if="error" variant="error" title="Gagal">{{ error }}</Alert>
    <Alert v-if="result" variant="success" :title="resultTitle">{{ resultDetail }}</Alert>

    <Card>
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-1.5">
          <label for="batch-key" class="text-sm font-medium text-slate-800">Key pair untuk semua dokumen</label>
          <select
            id="batch-key" v-model="keyPairId" required
            class="w-full rounded-md border border-light-blue bg-white px-3 py-2 focus:border-deep-blue focus:outline-none focus:ring-2 focus:ring-deep-blue/30"
          >
            <option value="" disabled>Pilih key pair…</option>
            <option v-for="k in activeKeys" :key="k.id" :value="k.id">
              {{ k.algorithm }}
            </option>
          </select>
          <p v-if="!activeKeys.length && !keysLoading" class="text-xs text-slate-500">
            Belum ada key aktif. Buat dulu di halaman detail permintaan.
          </p>
          <p v-if="keyError" role="alert" class="text-xs text-[#B3261E]">{{ keyError }}</p>
        </div>
        <div v-if="selectedKey" class="rounded-md border border-light-blue bg-white p-3">
          <div class="flex items-center justify-between gap-2">
            <p class="text-xs font-semibold text-deep-blue">
              Kunci publik ({{ selectedKey.algorithm }}) — dipakai untuk semua dokumen batch ini
            </p>
            <Button variant="ghost" size="sm" @click="copyKey">{{ copiedTick ? 'Tersalin!' : 'Salin' }}</Button>
          </div>
          <pre class="mt-2 max-h-24 overflow-auto whitespace-pre-wrap break-all rounded bg-slate-50 p-2 font-mono text-[10px] leading-relaxed text-slate-600">{{ selectedKey.publicKey }}</pre>
        </div>
        <div v-if="selectedIds.length === 0" class="rounded-md bg-cream p-4 text-sm text-brown">
          Belum ada yang dipilih. Centang dokumen di
          <RouterLink to="/signer" class="font-semibold underline">dashboard Signer</RouterLink>.
        </div>
        <ul v-else class="flex flex-col gap-2" aria-label="Dokumen terpilih">
          <li v-for="sid in selectedIds" :key="sid" class="flex items-center justify-between gap-2 rounded-md border border-cream bg-white px-3 py-2 text-sm">
            <span class="min-w-0">
              <span class="block truncate font-semibold">{{ docTitle(sid) }}</span>
              <span class="block truncate text-xs text-slate-500">{{ docSub(sid) }}</span>
            </span>
            <button type="button" class="shrink-0 text-xs font-semibold text-[#B3261E] hover:underline" :aria-label="`Hapus ${sid} dari batch`" @click="toggleSelect(sid)">
              Hapus
            </button>
          </li>
        </ul>
        <div class="flex justify-end gap-2">
          <Button variant="ghost" @click="clearSelection">Bersihkan</Button>
          <Button variant="accent" :loading="isLoading" :disabled="selectedIds.length === 0 || !keyPairId.trim()" @click="submit">
            Tandatangani {{ selectedIds.length }} dokumen
          </Button>
        </div>
      </div>
    </Card>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import Alert from '@/components/ui/Alert.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import { documentService, type KeyPairItem } from '@/services/documentService'
import { toApiMessage } from '@/services/apiClient'
import { useSignRequest } from '@/composables/useSignRequest'

const { pending, selectedIds, isLoading, error, fetchPending, toggleSelect, clearSelection, batchApprove, clearError } = useSignRequest()

const keyPairId = ref('')
const keys = ref<KeyPairItem[]>([])
const keysLoading = ref(true)
const keyError = ref('')
const copiedTick = ref(false)
const result = ref<{ ok: number; fail: number } | null>(null)
/** Cache judul dokumen per sign-request id (diambil sekali per item terpilih). */
const titles = ref<Record<string, string>>({})

const activeKeys = computed(() => keys.value.filter((k) => !k.revoked))
const selectedKey = computed(() => keys.value.find((k) => k.id === keyPairId.value) ?? null)

const resultTitle = computed(() => (result.value ? `Selesai: ${result.value.ok} sukses, ${result.value.fail} gagal` : ''))
const resultDetail = computed(() => {
  if (!result.value) return ''
  return result.value.fail === 0
    ? 'Semua dokumen berhasil ditandatangani. QR tertempel di tiap dokumen final.'
    : 'Sebagian gagal — periksa tabel pending untuk item yang tersisa.'
})

function formatDate(v: string): string {
  try {
    return new Date(v).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' })
  } catch {
    return v
  }
}

function requestOf(sid: string) {
  return pending.value.find((r) => r.id === sid)
}

function docTitle(sid: string): string {
  return titles.value[sid] ?? `${sid.slice(0, 12)}…`
}

function docSub(sid: string): string {
  const req = requestOf(sid)
  const when = req ? formatDate(req.updatedAt) : ''
  return titles.value[sid] ? `ID ${sid.slice(0, 12)}…${when ? ` • ${when}` : ''}` : `ID permintaan • ${when}`
}

async function copyKey() {
  if (!selectedKey.value) return
  try {
    await navigator.clipboard.writeText(selectedKey.value.publicKey)
  } catch {
    const ta = document.createElement('textarea')
    ta.value = selectedKey.value.publicKey
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    ta.remove()
  }
  copiedTick.value = true
  setTimeout(() => { copiedTick.value = false }, 2000)
}

async function loadKeys() {
  keysLoading.value = true
  keyError.value = ''
  try {
    const res = await documentService.listKeys()
    keys.value = res.data
  } catch (e) {
    keyError.value = toApiMessage(e, 'Daftar key gagal dimuat.')
    keys.value = []
  } finally {
    keysLoading.value = false
  }
}

/** Ambil judul dokumen untuk item terpilih (sekali per dokumen, abaikan yang gagal). */
async function loadTitles() {
  const missing = selectedIds.value.filter((sid) => !(sid in titles.value))
  await Promise.all(missing.map(async (sid) => {
    const req = requestOf(sid)
    if (!req) return
    try {
      const doc = await documentService.getDocument(req.documentId)
      titles.value[sid] = doc.title
    } catch {
      /* fallback ID + badge di template */
    }
  }))
}

async function submit() {
  result.value = null
  clearError()
  const items = selectedIds.value.map((signRequestId) => ({ signRequestId, keyPairId: keyPairId.value.trim() }))
  const res = await batchApprove(items)
  result.value = {
    ok: res.results.filter((r) => r.success).length,
    fail: res.results.filter((r) => !r.success).length,
  }
}

watch(selectedIds, () => { void loadTitles() }, { immediate: false })

onMounted(async () => {
  await fetchPending()
  await Promise.all([loadKeys(), loadTitles()])
})
</script>
