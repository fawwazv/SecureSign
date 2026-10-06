<template>
  <div v-if="bare" class="h-full w-full overflow-hidden bg-white">
    <iframe
      :src="viewSrc"
      :title="`Pratinjau PDF: ${title}`"
      class="h-full w-full bg-white"
      loading="lazy"
    >
      <p>Browser tidak mendukung pratinjau PDF. <a :href="src">Unduh dokumen</a>.</p>
    </iframe>
  </div>
  <div v-else class="overflow-hidden rounded-lg border border-cream bg-white shadow-sm">
    <div class="flex items-center justify-between bg-cream px-4 py-2">
      <p class="truncate text-sm font-semibold text-deep-blue">{{ title }}</p>
      <a
        :href="src"
        target="_blank"
        rel="noopener"
        class="text-xs font-semibold text-deep-blue hover:underline"
      >
        Buka di tab baru
      </a>
    </div>
    <iframe
      :src="viewSrc"
      :title="`Pratinjau PDF: ${title}`"
      class="h-[60vh] w-full bg-white"
      loading="lazy"
    >
      <p>Browser tidak mendukung pratinjau PDF. <a :href="src">Unduh dokumen</a>.</p>
    </iframe>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{ src: string; title: string; bare?: boolean }>(),
  { bare: false },
)

/**
 * Mode bare dipakai di dalam QrEditor: tanpa header kartu + tanpa toolbar
 * bawaan viewer agar area stage persis = area halaman PDF (fraksi QR akurat).
 * Fragment diabaikan browser yang tak mendukung — aman sebagai hint.
 */
const viewSrc = computed(() => (props.src ? `${props.src}#toolbar=0&navpanes=0` : props.src))
</script>
