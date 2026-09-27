<template>
  <Teleport to="body">
    <Transition name="sv-modal">
      <div
        v-if="open"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
        role="dialog"
        aria-modal="true"
        :aria-label="title"
        @click.self="$emit('close')"
      >
        <div class="w-full max-w-lg rounded-lg bg-white p-6 shadow-lg">
          <div class="mb-4 flex items-start justify-between gap-4">
            <h3 class="text-deep-blue">{{ title }}</h3>
            <button
              type="button"
              class="rounded-md p-1 text-slate-500 hover:bg-cream"
              aria-label="Tutup dialog"
              @click="$emit('close')"
            >
              <X class="h-5 w-5" />
            </button>
          </div>
          <slot />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { X } from 'lucide-vue-next'

defineProps<{ open: boolean; title: string }>()
defineEmits<{ (e: 'close'): void }>()
</script>

<style scoped>
.sv-modal-enter-active,
.sv-modal-leave-active {
  transition: opacity 0.15s ease;
}
.sv-modal-enter-from,
.sv-modal-leave-to {
  opacity: 0;
}
</style>
