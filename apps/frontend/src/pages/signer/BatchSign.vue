<template>
  <section aria-label="Batch signing" class="mx-auto flex max-w-3xl flex-col gap-4">
    <div>
      <h2 class="text-deep-blue">Batch Signing</h2>
      <p class="text-sm text-slate-500">Tandatangani banyak dokumen sekaligus dalam satu transaksi.</p>
    </div>

    <Alert v-if="error" variant="error" title="Gagal">{{ error }}</Alert>
    <Alert v-if="result" variant="success" :title="resultTitle">{{ resultDetail }}</Alert>

    <Card>
      <div class="flex flex-col gap-4">
        <Input id="batch-key" v-model="keyPairId" label="ID Key Pair untuk semua dokumen" placeholder="UUID key pair Anda" required />
        <div v-if="selectedIds.length === 0" class="rounded-md bg-cream p-4 text-sm text-brown">
          Belum ada yang dipilih. Centang dokumen di
          <RouterLink to="/signer" class="font-semibold underline">dashboard Signer</RouterLink>.
        </div>
        <ul v-else class="flex flex-col gap-2" aria-label="Dokumen terpilih">
          <li v-for="sid in selectedIds" :key="sid" class="flex items-center justify-between gap-2 rounded-md border border-cream bg-white px-3 py-2 text-sm">
            <span class="truncate">{{ sid }}</span>
            <button type="button" class="text-xs font-semibold text-[#B3261E] hover:underline" :aria-label="`Hapus ${sid} dari batch`" @click="toggleSelect(sid)">
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
import { computed, onMounted, ref } from 'vue'
import Alert from '@/components/ui/Alert.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Input from '@/components/ui/Input.vue'
import { useSignRequest } from '@/composables/useSignRequest'

const { selectedIds, isLoading, error, fetchPending, toggleSelect, clearSelection, batchApprove, clearError } = useSignRequest()

const keyPairId = ref('')
const result = ref<{ ok: number; fail: number } | null>(null)

const resultTitle = computed(() => (result.value ? `Selesai: ${result.value.ok} sukses, ${result.value.fail} gagal` : ''))
const resultDetail = computed(() => {
  if (!result.value) return ''
  return result.value.fail === 0
    ? 'Semua dokumen berhasil ditandatangani. QR tertempel di tiap dokumen final.'
    : 'Sebagian gagal — periksa tabel pending untuk item yang tersisa.'
})

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

onMounted(fetchPending)
</script>
