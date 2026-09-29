<template>
  <section aria-label="Audit log global" class="flex flex-col gap-4">
    <div>
      <h2 class="text-deep-blue">Audit Log Global</h2>
      <p class="text-sm text-slate-500">Immutable — tercatat untuk setiap aksi sign & verify. Total {{ auditTotal }} entri.</p>
    </div>
    <Alert v-if="error" variant="error" title="Gagal memuat">{{ error }}</Alert>
    <Card>
      <Table :columns="columns" :rows="auditRows" empty-text="Belum ada entri audit.">
        <template #cell(createdAt)="{ value }">{{ formatDate(String(value)) }}</template>
        <template #cell(details)="{ value }">{{ JSON.stringify(value) }}</template>
      </Table>
      <div v-if="totalPages > 1" class="mt-3 flex items-center justify-center gap-2">
        <Button variant="ghost" size="sm" :disabled="page <= 1" @click="goPage(page - 1)">Sebelumnya</Button>
        <span class="text-sm text-slate-600" role="status">Halaman {{ page }} / {{ totalPages }}</span>
        <Button variant="ghost" size="sm" :disabled="page >= totalPages" @click="goPage(page + 1)">Berikutnya</Button>
      </div>
    </Card>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import Alert from '@/components/ui/Alert.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Table from '@/components/ui/Table.vue'
import { useDocumentStore } from '@/stores/documentStore'

const store = useDocumentStore()
const columns = [
  { key: 'id', label: 'ID' },
  { key: 'action', label: 'Aksi' },
  { key: 'entity', label: 'Entitas' },
  { key: 'createdAt', label: 'Waktu' },
  { key: 'details', label: 'Detail' },
]

const error = computed(() => store.error)
const auditTotal = computed(() => store.auditTotal)
const page = computed(() => store.auditPage)
const totalPages = computed(() => Math.max(1, Math.ceil(store.auditTotal / store.auditLimit)))
const auditRows = computed(() => store.auditLogs as unknown as Array<Record<string, unknown>>)

function goPage(p: number) {
  store.auditPage = p
  store.fetchAuditLogs()
}

function formatDate(v: string): string {
  try {
    return new Date(v).toLocaleString('id-ID', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch {
    return v
  }
}

onMounted(() => store.fetchAuditLogs())
</script>
