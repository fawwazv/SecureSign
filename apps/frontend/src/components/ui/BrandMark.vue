<template>
  <span class="flex items-center gap-2">
    <img
      :src="logoSrc"
      alt="Logo SignVault"
      :class="imgClass"
      width="36"
      height="36"
    />
    <span class="leading-tight">
      <span class="block text-lg font-bold" :class="nameClass">SignVault</span>
      <span
        v-if="subtitle"
        class="block text-[10px] font-medium tracking-wider"
        :class="subtitleClass"
      >
        {{ subtitle }}
      </span>
    </span>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    /** Tema teks: samakan dengan latar (header/sidebar terang vs footer gelap). */
    variant?: 'dark' | 'light'
    /** Teks kecil di bawah nama, cth. "TANDA TANGAN DIGITAL". */
    subtitle?: string
    /** Ukuran logo: sm (sidebar) / md (header, default). */
    size?: 'sm' | 'md'
  }>(),
  { variant: 'dark', subtitle: '', size: 'md' },
)

const logoSrc = `${import.meta.env.BASE_URL}logo.png`
const imgClass = computed(() => (props.size === 'sm' ? 'h-8 w-8' : 'h-9 w-9'))
const nameClass = computed(() =>
  [props.variant === 'light' ? 'text-white' : 'text-deep-blue', props.size === 'sm' ? '!text-[15px]' : ''].join(' '),
)
const subtitleClass = computed(() =>
  props.variant === 'light' ? 'text-white/70' : 'text-slate-400',
)
</script>
