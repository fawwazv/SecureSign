<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" :for="id" class="text-sm font-medium text-slate-800">
      {{ label }} <span v-if="required" class="text-[#B3261E]" aria-hidden="true">*</span>
    </label>
    <input
      :id="id"
      :value="modelValue"
      :type="type"
      :placeholder="placeholder"
      :required="required"
      :disabled="disabled"
      :autocomplete="autocomplete"
      :aria-invalid="!!error"
      :aria-describedby="error ? `${id}-error` : undefined"
      :class="inputClass"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      @blur="$emit('blur')"
      v-bind="$attrs"
    />
    <p v-if="hint && !error" class="text-xs text-slate-500">{{ hint }}</p>
    <p v-if="error" :id="`${id}-error`" role="alert" class="text-xs text-[#B3261E]">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '@/utils/cn'

const props = withDefaults(
  defineProps<{
    id: string
    modelValue: string
    label?: string
    type?: string
    placeholder?: string
    hint?: string
    error?: string
    required?: boolean
    disabled?: boolean
    autocomplete?: string
  }>(),
  { type: 'text', required: false, disabled: false },
)

defineEmits<{
  (e: 'update:modelValue', v: string): void
  (e: 'blur'): void
}>()

const inputClass = computed(() =>
  cn(
    'w-full rounded-md border bg-white px-3 py-2 text-base text-slate-900 placeholder:text-slate-400',
    'border-light-blue focus:border-deep-blue focus:outline-none focus:ring-2 focus:ring-deep-blue/30',
    'disabled:cursor-not-allowed disabled:bg-slate-100',
    props.error && 'border-[#B3261E] focus:border-[#B3261E] focus:ring-[#B3261E]/20',
  ),
)
</script>
