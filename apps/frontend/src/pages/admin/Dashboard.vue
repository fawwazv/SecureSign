<template>
  <section aria-label="Dashboard Super Admin" class="flex flex-col gap-4">
    <div>
      <h2 class="text-deep-blue">Ringkasan Platform</h2>
      <p class="text-sm text-slate-500">Statistik global SignVault.</p>
    </div>
    <Alert v-if="error" variant="error" title="Gagal memuat">{{ error }}</Alert>
    <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <Card v-for="s in stats" :key="s.label" :title="s.value" :subtitle="s.label" />
    </div>
    <div class="flex flex-wrap gap-2">
      <RouterLink to="/admin/users"><Button variant="secondary" size="sm">Kelola user & key</Button></RouterLink>
      <RouterLink to="/admin/audit"><Button variant="ghost" size="sm">Lihat audit log</Button></RouterLink>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Alert from '@/components/ui/Alert.vue'
import { documentService } from '@/services/documentService'
import { toApiMessage } from '@/services/apiClient'
import { useDocumentStore } from '@/stores/documentStore'

const store = useDocumentStore()
const error = ref<string | null>(null)
const docTotal = ref(0)
const pendingTotal = ref(0)
const auditTotal = ref(0)

const stats = computed(() => [
  { label: 'Total dokumen', value: String(docTotal.value) },
  { label: 'Menunggu tanda tangan', value: String(pendingTotal.value) },
  { label: 'Entri audit log', value: String(auditTotal.value) },
  { label: 'Notifikasi aktif', value: String(store.notifications.length) },
])

onMounted(async () => {
  error.value = null
  try {
    const [docs, pending, audit] = await Promise.all([
      documentService.listDocuments({ page: 1, limit: 1 }),
      documentService.listPendingSignRequests({ page: 1, limit: 1 }),
      documentService.listAuditLogs({ page: 1, limit: 1 }),
    ])
    docTotal.value = docs.total
    pendingTotal.value = pending.total
    auditTotal.value = audit.total
    await store.fetchNotifications()
  } catch (e) {
    error.value = toApiMessage(e, 'Gagal memuat statistik.')
  }
})
</script>
