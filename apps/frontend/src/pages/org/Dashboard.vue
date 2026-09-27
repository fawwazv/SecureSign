<template>
  <section aria-label="Dashboard Org Admin" class="flex flex-col gap-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 class="text-deep-blue">Dokumen Saya</h2>
        <p class="text-sm text-slate-500">{{ total }} dokumen · klik baris untuk detail</p>
      </div>
      <RouterLink to="/org/upload">
        <Button variant="primary" size="sm"><Upload class="h-4 w-4" aria-hidden="true" /> Upload PDF</Button>
      </RouterLink>
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

    <div v-if="isLoading" class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3" aria-busy="true" aria-label="Memuat dokumen">
      <Card v-for="i in 3" :key="i"><p class="text-sm text-slate-400">Memuat…</p></Card>
    </div>

    <div v-else-if="documents.length === 0" class="rounded-lg bg-white p-8 text-center shadow-sm">
      <p class="font-semibold text-deep-blue">Belum ada dokumen</p>
      <p class="mt-1 text-sm text-slate-500">Upload PDF pertama Anda untuk memulai alur tanda tangan.</p>
      <RouterLink to="/org/upload" class="mt-4 inline-block">
        <Button variant="accent" size="sm">Upload sekarang</Button>
      </RouterLink>
    </div>

    <div v-else class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      <DocumentCard v-for="doc in documents" :key="doc.id" :document="doc">
        <template #actions>
          <RouterLink :to="`/org/documents/${doc.id}`">
            <Button variant="secondary" size="sm">Detail</Button>
          </RouterLink>
          <Button
            v-if="doc.status === 'DRAFT'"
            variant="ghost"
            size="sm"
            @click="quickRequest(doc.id)"
          >
            Minta tanda tangan
          </Button>
        </template>
      </DocumentCard>
    </div>

    <div v-if="totalPages > 1" class="flex items-center justify-center gap-2">
      <Button variant="ghost" size="sm" :disabled="page <= 1" @click="goPage(page - 1)">Sebelumnya</Button>
      <span class="text-sm text-slate-600" role="status">Halaman {{ page }} / {{ totalPages }}</span>
      <Button variant="ghost" size="sm" :disabled="page >= totalPages" @click="goPage(page + 1)">Berikutnya</Button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Upload } from 'lucide-vue-next'
import Alert from '@/components/ui/Alert.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import DocumentCard from '@/components/domain/DocumentCard.vue'
import { useDocument } from '@/composables/useDocument'
import { useDocumentStore } from '@/stores/documentStore'
import type { DocumentStatus } from '@/services/documentService'

const { documents, documentsTotal, documentsPage, statusFilter, isLoading, error, setStatusFilter, fetchDocuments, clearError } = useDocument()
const store = useDocumentStore()
const router = useRouter()

const filters: Array<{ label: string; value: DocumentStatus | '' }> = [
  { label: 'Semua', value: '' },
  { label: 'Draf', value: 'DRAFT' },
  { label: 'Menunggu', value: 'PENDING' },
  { label: 'Ditandatangani', value: 'SIGNED' },
  { label: 'Ditolak', value: 'REJECTED' },
]

const total = computed(() => documentsTotal.value)
const page = computed(() => documentsPage.value)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / store.documentsLimit)))

function applyFilter(v: DocumentStatus | '') {
  clearError()
  setStatusFilter(v)
  fetchDocuments()
}

function goPage(p: number) {
  store.documentsPage = p
  fetchDocuments()
}

function quickRequest(id: string) {
  router.push(`/org/documents/${id}?request=1`)
}

onMounted(fetchDocuments)
</script>
