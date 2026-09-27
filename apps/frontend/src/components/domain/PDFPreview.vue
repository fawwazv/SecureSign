<template>
  <div class="overflow-hidden rounded-lg border border-cream bg-white shadow-sm">
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
      :src="src"
      :title="`Pratinjau PDF: ${title}`"
      class="h-[60vh] w-full bg-white"
      loading="lazy"
    >
      <p>Browser tidak mendukung pratinjau PDF. <a :href="src">Unduh dokumen</a>.</p>
    </iframe>
  </div>
</template>

<script setup lang="ts">
defineProps<{ src: string; title: string }>()
</script>
