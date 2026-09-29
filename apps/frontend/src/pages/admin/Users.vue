<template>
  <section aria-label="Manajemen user dan kunci" class="flex flex-col gap-4">
    <div>
      <h2 class="text-deep-blue">Manajemen User & Key</h2>
      <p class="text-sm text-slate-500">Revoke key pair yang bocor. Rotasi = revoke + generate baru oleh pemilik key.</p>
    </div>
    <Alert v-if="error" variant="error" title="Gagal memuat">{{ error }}</Alert>
    <Alert v-if="notice" variant="success" title="Berhasil">{{ notice }}</Alert>
    <Alert variant="warning" title="Catatan kontrak API">
      OpenAPI v0.1 hanya menyediakan <code>GET /users/me</code> — daftar user global belum ada di backend.
      Tabel di bawah menampilkan key pair (revoke didukung <code>POST /keys/{id}/revoke</code>).
    </Alert>
    <Card title="Key Pair">
      <Table :columns="columns" :rows="keyRows" empty-text="Belum ada key pair.">
        <template #cell(revoked)="{ value }">
          <Badge :tone="value ? 'rejected' : 'signed'">{{ value ? 'REVOKED' : 'AKTIF' }}</Badge>
        </template>
        <template #cell(actions)="{ row }">
          <Button
            variant="danger"
            size="sm"
            :disabled="Boolean(row.revoked)"
            :loading="revokingId === String(row.id)"
            @click="revoke(String(row.id))"
          >
            Revoke
          </Button>
        </template>
      </Table>
    </Card>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import Alert from '@/components/ui/Alert.vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Table from '@/components/ui/Table.vue'
import { documentService, type KeyPairItem } from '@/services/documentService'
import { toApiMessage } from '@/services/apiClient'

const keys = ref<KeyPairItem[]>([])
const error = ref<string | null>(null)
const notice = ref('')
const revokingId = ref<string | null>(null)

const columns = [
  { key: 'id', label: 'ID' },
  { key: 'algorithm', label: 'Algoritma' },
  { key: 'revoked', label: 'Status' },
  { key: 'createdAt', label: 'Dibuat' },
  { key: 'actions', label: 'Aksi' },
]
const keyRows = computed(() => keys.value as unknown as Array<Record<string, unknown>>)

async function load() {
  error.value = null
  try {
    const res = await documentService.listKeys()
    keys.value = res.data
  } catch (e) {
    error.value = toApiMessage(e, 'Gagal memuat key pair.')
  }
}

async function revoke(id: string) {
  notice.value = ''
  revokingId.value = id
  try {
    await documentService.revokeKey(id)
    notice.value = `Key ${id} di-revoke. Minta pemilik generate key baru untuk rotasi.`
    await load()
  } catch (e) {
    error.value = toApiMessage(e, 'Revoke key gagal.')
  } finally {
    revokingId.value = null
  }
}

onMounted(load)
</script>
