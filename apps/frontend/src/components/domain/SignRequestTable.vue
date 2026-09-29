<template>
  <Table :columns="columns" :rows="tableRows" :empty-text="emptyText">
    <template v-if="selectable" #cell(select)="{ row }">
      <input
        type="checkbox"
        :checked="selectedIds.includes(String(row.id))"
        :disabled="row.status !== 'PENDING'"
        :aria-label="`Pilih permintaan ${String(row.id)}`"
        class="h-4 w-4 accent-[#326080]"
        @change="$emit('toggle', String(row.id))"
      />
    </template>
    <template #cell(status)="{ value }">
      <Badge :tone="statusTone(value as string)">{{ value }}</Badge>
    </template>
    <template #cell(updatedAt)="{ value }">
      {{ formatDate(value as string) }}
    </template>
    <template #cell(actions)="{ row }">
      <slot name="actions" :row="row" />
    </template>
  </Table>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import Badge from '@/components/ui/Badge.vue'
import Table from '@/components/ui/Table.vue'
import type { SignRequestItem } from '@/services/documentService'

const props = withDefaults(
  defineProps<{
    rows: SignRequestItem[]
    selectable?: boolean
    selectedIds?: string[]
    emptyText?: string
  }>(),
  { selectable: false, selectedIds: () => [], emptyText: 'Belum ada permintaan tanda tangan.' },
)

defineEmits<{ (e: 'toggle', id: string): void }>()

/** Table FE1 mensyaratkan Record<string, unknown>; interface domain di-cast di batas ini saja. */
const tableRows = computed(() => props.rows as unknown as Array<Record<string, unknown>>)

const columns = computed(() => [
  ...(props.selectable ? [{ key: 'select', label: '' }] : []),
  { key: 'id', label: 'ID' },
  { key: 'documentId', label: 'Dokumen' },
  { key: 'status', label: 'Status' },
  { key: 'updatedAt', label: 'Diperbarui' },
  { key: 'actions', label: 'Aksi' },
])

function statusTone(status: string): 'pending' | 'signed' | 'rejected' | 'neutral' {
  if (status === 'PENDING') return 'pending'
  if (status === 'APPROVED') return 'signed'
  if (status === 'REJECTED') return 'rejected'
  return 'neutral'
}

function formatDate(value: string): string {
  try {
    return new Date(value).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' })
  } catch {
    return value
  }
}
</script>
