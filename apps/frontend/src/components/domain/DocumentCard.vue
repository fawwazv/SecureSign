<template>
  <Card class="flex flex-col gap-3">
    <div class="flex items-start justify-between gap-3">
      <div class="min-w-0">
        <h3 class="truncate text-deep-blue">{{ document.title }}</h3>
        <p v-if="document.description" class="mt-1 line-clamp-2 text-sm text-slate-500">{{ document.description }}</p>
      </div>
      <Badge :tone="tone">{{ document.status }}</Badge>
    </div>
    <dl class="grid grid-cols-2 gap-2 text-xs text-slate-600">
      <div>
        <dt class="font-semibold text-deep-blue">Hash SHA-256</dt>
        <dd class="truncate" :title="document.fileHash">{{ shortHash }}</dd>
      </div>
      <div>
        <dt class="font-semibold text-deep-blue">Diperbarui</dt>
        <dd>{{ formattedDate }}</dd>
      </div>
    </dl>
    <div class="flex flex-wrap gap-2">
      <slot name="actions" />
    </div>
  </Card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import Badge from '@/components/ui/Badge.vue'
import Card from '@/components/ui/Card.vue'
import type { DocumentItem } from '@/services/documentService'

const props = defineProps<{ document: DocumentItem }>()

const tone = computed(() => {
  switch (props.document.status) {
    case 'DRAFT':
      return 'draft' as const
    case 'PENDING':
      return 'pending' as const
    case 'SIGNED':
      return 'signed' as const
    case 'REJECTED':
      return 'rejected' as const
  }
})

const shortHash = computed(() =>
  props.document.fileHash.length > 18
    ? `${props.document.fileHash.slice(0, 10)}…${props.document.fileHash.slice(-6)}`
    : props.document.fileHash,
)

const formattedDate = computed(() => {
  try {
    return new Date(props.document.updatedAt).toLocaleDateString('id-ID', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    })
  } catch {
    return props.document.updatedAt
  }
})
</script>
