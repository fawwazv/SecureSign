<template>
  <div>
    <div role="tablist" :aria-label="label" class="flex gap-1 rounded-md bg-cream p-1">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        role="tab"
        :aria-selected="modelValue === tab.value"
        :class="[
          'flex-1 rounded-md px-4 py-2 text-sm font-semibold transition-colors',
          modelValue === tab.value ? 'bg-white text-deep-blue shadow-sm' : 'text-slate-600 hover:text-deep-blue',
        ]"
        @click="$emit('update:modelValue', tab.value)"
      >
        {{ tab.label }}
      </button>
    </div>
    <div class="mt-4" role="tabpanel">
      <slot :name="modelValue" />
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    modelValue: string
    tabs: Array<{ value: string; label: string }>
    label?: string
  }>(),
  { label: 'Tabs' },
)

defineEmits<{ (e: 'update:modelValue', v: string): void }>()
</script>
