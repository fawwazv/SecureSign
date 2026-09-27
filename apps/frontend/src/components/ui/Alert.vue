<template>
  <div :class="classes" role="alert">
    <component :is="icon" class="h-5 w-5 shrink-0" aria-hidden="true" />
    <div class="min-w-0">
      <p v-if="title" class="font-semibold">{{ title }}</p>
      <p class="text-sm"><slot /></p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { CircleAlert, CircleCheck, Info, TriangleAlert } from 'lucide-vue-next'
import { cn } from '@/utils/cn'

const props = withDefaults(defineProps<{ variant?: 'info' | 'success' | 'warning' | 'error'; title?: string }>(), {
  variant: 'info',
})

const icon = computed(() => ({ info: Info, success: CircleCheck, warning: TriangleAlert, error: CircleAlert })[props.variant])

const classes = computed(() =>
  cn('flex items-start gap-3 rounded-md border p-4', {
    info: 'border-light-blue bg-light-blue/40 text-deep-blue',
    success: 'border-green-200 bg-green-50 text-[#1B7A3D]',
    warning: 'border-brown/30 bg-cream text-brown',
    error: 'border-red-200 bg-red-50 text-[#B3261E]',
  }[props.variant]),
)
</script>
