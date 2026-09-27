<template>
  <div :class="cn('sv-card p-6', $attrs.class as string)">
    <div v-if="$slots.header || title" class="mb-4">
      <slot name="header">
        <h3 v-if="title" class="text-deep-blue">{{ title }}</h3>
        <p v-if="subtitle" class="mt-1 text-sm text-slate-500">{{ subtitle }}</p>
      </slot>
    </div>
    <slot />
    <div v-if="$slots.footer" class="mt-4 border-t border-cream pt-4">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { cn } from '@/utils/cn'

defineProps<{ title?: string; subtitle?: string }>()
</script>
