<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :class="classes"
    v-bind="$attrs"
  >
    <Loader2 v-if="loading" class="h-4 w-4 animate-spin" aria-hidden="true" />
    <slot />
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Loader2 } from 'lucide-vue-next'
import { cn } from '@/utils/cn'

const props = withDefaults(
  defineProps<{
    variant?: 'primary' | 'secondary' | 'accent' | 'ghost' | 'danger' | 'outline'
    size?: 'sm' | 'md' | 'lg'
    type?: 'button' | 'submit' | 'reset'
    disabled?: boolean
    loading?: boolean
    block?: boolean
  }>(),
  { variant: 'primary', size: 'md', type: 'button', disabled: false, loading: false, block: false },
)

const classes = computed(() =>
  cn(
    'inline-flex items-center justify-center gap-2 font-semibold transition-colors',
    'rounded-md focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-deep-blue',
    'disabled:cursor-not-allowed disabled:opacity-50',
    props.block && 'w-full',
    {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-base',
      lg: 'px-6 py-3 text-base',
    }[props.size],
    {
      primary: 'bg-deep-blue text-white hover:bg-deep-blue-dark',
      secondary: 'bg-light-blue text-deep-blue hover:bg-[#9CC2DA]',
      accent: 'bg-brown text-white hover:bg-brown-dark',
      ghost: 'bg-transparent text-deep-blue hover:bg-cream',
      danger: 'bg-[#B3261E] text-white hover:bg-[#8F1D17]',
      outline: 'border border-light-blue bg-white text-deep-blue hover:bg-cream',
    }[props.variant],
  ),
)
</script>
