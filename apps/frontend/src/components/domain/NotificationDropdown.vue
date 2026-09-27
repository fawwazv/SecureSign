<template>
  <div class="rounded-lg bg-white p-2 shadow-lg" role="region" aria-label="Notifikasi">
    <div class="flex items-center justify-between px-2 py-1">
      <p class="text-sm font-semibold text-deep-blue">Notifikasi</p>
      <button type="button" class="text-xs font-semibold text-deep-blue hover:underline" @click="$emit('read-all')">
        Tandai dibaca
      </button>
    </div>
    <p v-if="items.length === 0" class="px-2 py-4 text-center text-sm text-slate-500">Tidak ada notifikasi.</p>
    <ul v-else class="max-h-80 overflow-auto">
      <li
        v-for="item in items"
        :key="item.id"
        class="flex items-start gap-2 rounded-md px-2 py-2 hover:bg-cream"
      >
        <span
          class="mt-1.5 h-2 w-2 shrink-0 rounded-full"
          :class="item.read ? 'bg-slate-300' : 'bg-brown'"
          aria-hidden="true"
        />
        <div class="min-w-0">
          <p class="text-sm font-semibold">{{ item.title }}</p>
          <p v-if="item.message" class="truncate text-xs text-slate-600">{{ item.message }}</p>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
export interface NotificationEntry {
  id: string
  title: string
  message?: string
  read: boolean
}

defineProps<{ items: NotificationEntry[] }>()
defineEmits<{ (e: 'read-all'): void }>()
</script>
