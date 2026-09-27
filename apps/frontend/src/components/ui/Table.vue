<template>
  <div class="overflow-x-auto rounded-lg border border-cream bg-white shadow-sm">
    <table class="w-full text-left text-sm">
      <thead>
        <tr class="bg-cream text-deep-blue">
          <th
            v-for="col in columns"
            :key="col.key"
            scope="col"
            class="whitespace-nowrap px-4 py-3 font-semibold"
          >
            {{ col.label }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="rows.length === 0">
          <td :colspan="columns.length" class="px-4 py-8 text-center text-slate-500">
            {{ emptyText }}
          </td>
        </tr>
        <tr
          v-for="(row, i) in rows"
          :key="i"
          class="border-t border-cream hover:bg-cream/50"
        >
          <td v-for="col in columns" :key="col.key" class="px-4 py-3">
            <slot :name="`cell(${col.key})`" :row="row" :value="row[col.key]">
              {{ row[col.key] }}
            </slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts" generic="T extends Record<string, unknown>">
withDefaults(
  defineProps<{
    columns: Array<{ key: string; label: string }>
    rows: T[]
    emptyText?: string
  }>(),
  { emptyText: 'Belum ada data.' },
)
</script>
