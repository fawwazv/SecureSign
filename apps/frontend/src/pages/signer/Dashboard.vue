<template>
  <section aria-label="Dashboard Signer" class="flex flex-col gap-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-3">
        <h2 class="text-deep-blue">Permintaan Tanda Tangan</h2>
        <span
          class="inline-flex min-h-6 min-w-6 items-center justify-center rounded-full bg-brown px-2 text-sm font-bold text-white"
          role="status"
          :aria-label="`${pendingTotal} dokumen menunggu`"
        >
          {{ pendingTotal }} Menunggu
        </span>
      </div>
      <RouterLink to="/signer/batch">
        <Button variant="accent" size="sm" :disabled="!hasSelection">
          Batch sign ({{ selectedIds.length }})
        </Button>
      </RouterLink>
    </div>

    <Alert v-if="error" variant="error" title="Gagal memuat">{{ error }}</Alert>
    <Alert v-if="notice" variant="success" title="Berhasil">{{ notice }}</Alert>

    <Card>
      <div class="mb-3 flex flex-wrap items-center gap-2">
        <div class="flex min-w-52 flex-col gap-1.5">
          <label for="keypair-id" class="text-sm font-medium text-slate-800">Key pair aktif</label>
          <select
            id="keypair-id" v-model="keyPairId"
            class="w-full rounded-md border border-light-blue bg-white px-3 py-2 text-sm focus:border-deep-blue focus:outline-none focus:ring-2 focus:ring-deep-blue/30"
          >
            <option value="" disabled>Pilih key pair…</option>
            <option v-for="k in activeKeys" :key="k.id" :value="k.id">
              {{ k.algorithm }}
            </option>
          </select>
          <p v-if="!activeKeys.length && !keysLoading" class="text-xs text-slate-500">
            Belum ada key aktif. Buat di halaman detail permintaan.
          </p>
          <p v-if="keyError" role="alert" class="text-xs text-[#B3261E]">{{ keyError }}</p>
        </div>
      </div>
      <SignRequestTable
        :rows="pending"
        selectable
        :selected-ids="selectedIds"
        empty-text="Tidak ada dokumen menunggu. Kerja bagus!"
        @toggle="toggleSelect"
      >
        <template #actions="{ row }">
          <div class="flex gap-1">
            <RouterLink :to="`/signer/requests/${String(row.id)}`">
              <Button variant="secondary" size="sm">Review</Button>
            </RouterLink>
            <Button variant="primary" size="sm" :disabled="!keyPairId.trim()" :loading="actingId === String(row.id)" @click="approveOne(String(row.id))">
              Tandatangani
            </Button>
          </div>
        </template>
      </SignRequestTable>
    </Card>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import Alert from '@/components/ui/Alert.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import SignRequestTable from '@/components/domain/SignRequestTable.vue'
import { documentService, type KeyPairItem } from '@/services/documentService'
import { toApiMessage } from '@/services/apiClient'
import { useSignRequest } from '@/composables/useSignRequest'

const { pending, pendingTotal, selectedIds, hasSelection, error, fetchPending, toggleSelect, approve, clearError } = useSignRequest()

const keyPairId = ref('')
const keys = ref<KeyPairItem[]>([])
const keysLoading = ref(true)
const keyError = ref('')
const activeKeys = computed(() => keys.value.filter((k) => !k.revoked))
const notice = ref('')
const actingId = ref<string | null>(null)

async function approveOne(id: string) {
  notice.value = ''
  clearError()
  if (!keyPairId.value.trim()) return
  actingId.value = id
  try {
    await approve(id, keyPairId.value.trim())
    notice.value = 'Dokumen ditandatangani. QR tertempel di dokumen final.'
  } catch (e) {
    notice.value = ''
    void toApiMessage(e, '')
  } finally {
    actingId.value = null
  }
}

onMounted(async () => {
  await fetchPending()
  try {
    const res = await documentService.listKeys()
    keys.value = res.data
  } catch (e) {
    keyError.value = toApiMessage(e, 'Daftar key gagal dimuat.')
    keys.value = []
  } finally {
    keysLoading.value = false
  }
})
</script>
