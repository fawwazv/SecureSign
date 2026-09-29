<template>
  <section aria-label="Dashboard Sekretariat" class="flex flex-col gap-5">
    <div>
      <h2 class="text-xl font-bold text-slate-900">Dashboard</h2>
      <p class="mt-1 text-sm text-slate-500">Ringkasan aktivitas penandatanganan dokumen — {{ today }}</p>
    </div>

    <Alert v-if="error" variant="error" title="Gagal memuat">{{ error }}</Alert>

    <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <button
        v-for="card in cards"
        :key="card.label"
        type="button"
        :aria-pressed="tableFilter === card.status"
        class="block rounded-lg border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:-translate-y-0.5 focus-visible:outline-2 focus-visible:outline-deep-blue"
        @click="setTableFilter(card.status)"
      >
        <p class="text-[11px] font-semibold uppercase tracking-wider text-slate-500">{{ card.label }}</p>
        <p class="mt-2 text-3xl font-bold" :class="card.valueClass" role="status">
          {{ isLoading ? '…' : card.value }}
        </p>
        <p class="mt-1 text-xs text-slate-500">{{ card.hint }}</p>
      </button>
    </div>

    <div class="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 class="font-bold text-slate-900">{{ tableTitle }}</h3>
          <p class="text-xs text-slate-500">{{ displayRows.length }} dokumen ditampilkan</p>
        </div>
        <div class="flex gap-2">
          <Button v-if="tableFilter" variant="ghost" size="sm" @click="setTableFilter('')">Tampilkan semua</Button>
          <RouterLink to="/org/upload">
            <Button variant="primary" size="sm">+ Unggah Dokumen</Button>
          </RouterLink>
        </div>
      </div>
      <p v-if="isLoading || tableLoading" class="p-4 text-sm text-slate-400" aria-busy="true">Memuat dokumen…</p>
      <Table v-else :columns="columns" :rows="displayRows" empty-text="Belum ada dokumen pada filter ini.">
        <template #cell(title)="{ row }">
          <p class="font-semibold text-slate-900">{{ String(row.title) }}</p>
          <p v-if="row.description" class="max-w-64 truncate text-xs text-slate-500">{{ String(row.description) }}</p>
        </template>
        <template #cell(status)="{ value }">
          <Badge :tone="statusTone(value as string)">{{ statusLabel(value as string) }}</Badge>
        </template>
        <template #cell(createdAt)="{ value }">
          {{ formatDate(value as string) }}
        </template>
        <template #cell(actions)="{ row }">
          <RouterLink :to="`/org/documents/${String(row.id)}`" class="text-xs font-semibold text-deep-blue hover:underline">
            Lihat Detail
          </RouterLink>
        </template>
      </Table>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import Alert from '@/components/ui/Alert.vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Table from '@/components/ui/Table.vue'
import { documentService, type DocumentItem, type DocumentStatus } from '@/services/documentService'
import { toApiMessage } from '@/services/apiClient'

type Row = Record<string, unknown>

const stats = ref({ total: 0, signed: 0, pending: 0, rejected: 0 })
const recent = ref<Row[]>([])
const tableFilter = ref<DocumentStatus | ''>('')
const tableRows = ref<Row[]>([])
const tableLoading = ref(false)
const isLoading = ref(true)
const error = ref<string | null>(null)

const today = computed(() =>
  new Date().toLocaleDateString('id-ID', { day: 'numeric', month: 'long', year: 'numeric' }),
)

const cards = computed(() => [
  { label: 'Total Dokumen', value: stats.value.total, hint: 'Keseluruhan dokumen', status: '' as DocumentStatus | '', valueClass: 'text-slate-900' },
  { label: 'Ditandatangani', value: stats.value.signed, hint: 'Selesai diproses', status: 'SIGNED' as DocumentStatus | '', valueClass: 'text-[#1B7A3D]' },
  { label: 'Dalam Proses', value: stats.value.pending, hint: 'Menunggu penyelesaian', status: 'PENDING' as DocumentStatus | '', valueClass: 'text-brown' },
  { label: 'Ditolak', value: stats.value.rejected, hint: 'Memerlukan tindakan', status: 'REJECTED' as DocumentStatus | '', valueClass: 'text-slate-900' },
])

const tableTitle = computed(() => {
  if (tableFilter.value === 'SIGNED') return 'Dokumen — Ditandatangani'
  if (tableFilter.value === 'PENDING') return 'Dokumen — Dalam Proses'
  if (tableFilter.value === 'REJECTED') return 'Dokumen — Ditolak'
  if (tableFilter.value === 'DRAFT') return 'Dokumen — Draf'
  return 'Dokumen Terbaru'
})

const displayRows = computed(() => (tableFilter.value ? tableRows.value : recent.value))

const columns = [
  { key: 'title', label: 'Nama Berkas' },
  { key: 'status', label: 'Status' },
  { key: 'createdAt', label: 'Dibuat' },
  { key: 'actions', label: 'Aksi' },
]

function statusTone(status: string): 'pending' | 'signed' | 'rejected' | 'neutral' | 'draft' {
  if (status === 'PENDING') return 'pending'
  if (status === 'SIGNED') return 'signed'
  if (status === 'REJECTED') return 'rejected'
  if (status === 'DRAFT') return 'draft'
  return 'neutral'
}

function statusLabel(status: string): string {
  if (status === 'PENDING') return 'Dalam Proses'
  if (status === 'SIGNED') return 'Ditandatangani'
  if (status === 'REJECTED') return 'Ditolak'
  if (status === 'DRAFT') return 'Draf'
  return status
}

function formatDate(value: string): string {
  try {
    return new Date(value).toLocaleString('id-ID', {
      day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
    })
  } catch {
    return value
  }
}

async function count(status: DocumentStatus | ''): Promise<number> {
  const res = await documentService.listDocuments({ page: 1, limit: 1, status })
  return res.total
}

/** Klik kartu statistik = filter tabel di halaman ini (tetap di /org). */
async function setTableFilter(status: DocumentStatus | '') {
  tableFilter.value = status
  if (!status) return
  tableLoading.value = true
  try {
    const res = await documentService.listDocuments({ page: 1, limit: 10, status })
    tableRows.value = (res.data as DocumentItem[]).map((d) => ({ ...(d as unknown as Row) }))
  } catch (e) {
    error.value = toApiMessage(e, 'Daftar dokumen gagal dimuat.')
  } finally {
    tableLoading.value = false
  }
}

async function load() {
  isLoading.value = true
  error.value = null
  try {
    const [total, signed, pending, rejected, latest] = await Promise.all([
      count(''),
      count('SIGNED'),
      count('PENDING'),
      count('REJECTED'),
      documentService.listDocuments({ page: 1, limit: 5 }),
    ])
    stats.value = { total, signed, pending, rejected }
    recent.value = (latest.data as DocumentItem[]).map((d) => ({ ...(d as unknown as Row) }))
  } catch (e) {
    error.value = toApiMessage(e, 'Ringkasan dokumen gagal dimuat.')
  } finally {
    isLoading.value = false
  }
}

onMounted(load)
</script>
