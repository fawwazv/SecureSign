<template>
  <section aria-label="Daftar dokumen" class="flex flex-col gap-4">
    <div>
      <h2 class="text-deep-blue">{{ title }}</h2>
      <p class="text-sm text-slate-500">{{ total }} dokumen</p>
    </div>

    <Alert v-if="error" variant="error" title="Gagal memuat">{{ error }}</Alert>

    <div class="flex flex-wrap gap-2" role="group" aria-label="Filter status">
      <Button
        v-for="opt in filters"
        :key="opt.value"
        size="sm"
        :variant="statusFilter === opt.value ? 'primary' : 'secondary'"
        @click="applyFilter(opt.value)"
      >
        {{ opt.label }}
      </Button>
    </div>

    <Card>
      <p v-if="isLoading" class="p-4 text-sm text-slate-400" aria-busy="true">Memuat dokumen…</p>
      <Table v-else :columns="columns" :rows="rows" empty-text="Tidak ada dokumen pada filter ini.">
        <template #cell(title)="{ row }">
          <p class="font-semibold">{{ String(row.title) }}</p>
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
    </Card>

    <div v-if="totalPages > 1" class="flex items-center justify-center gap-2">
      <Button variant="ghost" size="sm" :disabled="page <= 1" @click="goPage(page - 1)">Sebelumnya</Button>
      <span class="text-sm text-slate-600" role="status">Halaman {{ page }} / {{ totalPages }}</span>
      <Button variant="ghost" size="sm" :disabled="page >= totalPages" @click="goPage(page + 1)">Berikutnya</Button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import Alert from '@/components/ui/Alert.vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Table from '@/components/ui/Table.vue'
import { useDocument } from '@/composables/useDocument'
import { useDocumentStore } from '@/stores/documentStore'
import type { DocumentStatus } from '@/services/documentService'

const { documents, documentsTotal, documentsPage, statusFilter, isLoading, error, setStatusFilter, fetchDocuments, clearError } = useDocument()
const store = useDocumentStore()
const route = useRoute()

const filters: Array<{ label: string; value: DocumentStatus | '' }> = [
  { label: 'Semua', value: '' },
  { label: 'Draf', value: 'DRAFT' },
  { label: 'Menunggu', value: 'PENDING' },
  { label: 'Ditandatangani', value: 'SIGNED' },
  { label: 'Ditolak', value: 'REJECTED' },
]

const columns = [
  { key: 'title', label: 'Nama Berkas' },
  { key: 'status', label: 'Status' },
  { key: 'createdAt', label: 'Dibuat' },
  { key: 'actions', label: 'Aksi' },
]

const total = computed(() => documentsTotal.value)
const page = computed(() => documentsPage.value)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / store.documentsLimit)))
const rows = computed(() => documents.value.map((d) => ({ ...(d as unknown as Record<string, unknown>) })))

const title = computed(() => {
  const found = filters.find((f) => f.value === statusFilter.value)
  return found && found.value ? `Dokumen — ${found.label}` : 'Semua Dokumen'
})

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

function applyFilter(v: DocumentStatus | '') {
  clearError()
  setStatusFilter(v)
  store.documentsPage = 1
  fetchDocuments()
}

function goPage(p: number) {
  store.documentsPage = p
  fetchDocuments()
}

function syncFromQuery() {
  const q = typeof route.query.status === 'string' ? route.query.status : ''
  const valid = (['', 'DRAFT', 'PENDING', 'SIGNED', 'REJECTED'] as const).includes(q as never)
  setStatusFilter(valid ? (q as DocumentStatus | '') : '')
  store.documentsPage = 1
}

watch(() => route.query.status, () => {
  syncFromQuery()
  fetchDocuments()
})

onMounted(() => {
  syncFromQuery()
  fetchDocuments()
})
</script>
