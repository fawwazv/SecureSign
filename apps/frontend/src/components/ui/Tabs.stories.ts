import type { Meta, StoryObj } from '@storybook/vue3'
import { ref } from 'vue'
import Tabs from './Tabs.vue'

const meta: Meta<typeof Tabs> = {
  title: 'UI/Tabs',
  component: Tabs,
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof Tabs>

export const VerifyMethods: Story = {
  args: {
    modelValue: 'upload',
    tabs: [
      { value: 'upload', label: 'Upload PDF' },
      { value: 'token', label: 'Token / QR' },
      { value: 'scan', label: 'Scan QR' },
    ],
  },
  render: (args) => ({
    components: { Tabs },
    setup: () => {
      const active = ref('upload')
      return { args, active }
    },
    template: `
      <Tabs v-model="active" :tabs="args.tabs">
        <template #upload><p class="text-sm">Panel upload PDF.</p></template>
        <template #token><p class="text-sm">Panel token QR.</p></template>
        <template #scan><p class="text-sm">Panel scan kamera.</p></template>
      </Tabs>`,
  }),
}
