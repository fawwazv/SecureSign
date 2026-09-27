<template>
  <span :class="classes" role="status"><slot /></span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '@/utils/cn'

const props = withDefaults(defineProps<{ tone?: 'draft' | 'pending' | 'signed' | 'rejected' | 'info' | 'neutral' }>(), {
  tone: 'neutral',
})

const classes = computed(() =>
  cn('inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold', {
    draft: 'bg-slate-200 text-slate-700',
    pending: 'bg-light-blue text-deep-blue',
    signed: 'bg-green-100 text-[#1B7A3D]',
    rejected: 'bg-red-100 text-[#B3261E]',
    info: 'bg-light-blue text-deep-blue',
    neutral: 'bg-cream text-brown',
  }[props.tone]),
)
</script>
