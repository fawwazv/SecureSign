import type { Meta, StoryObj } from '@storybook/vue3'
import Card from './Card.vue'
import Button from './Button.vue'

const meta: Meta<typeof Card> = {
  title: 'UI/Card',
  component: Card,
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof Card>

export const Basic: Story = {
  args: { title: 'Kontrak_Kerja.pdf', subtitle: 'Diunggah 27 Sep 2026' },
  render: (args) => ({
    components: { Card, Button },
    setup: () => ({ args }),
    template: `
      <Card v-bind="args">
        <p class="text-sm text-slate-600">Isi kartu: metadata dokumen, status, dan aksi.</p>
        <template #footer><Button variant="secondary" size="sm">Lihat detail</Button></template>
      </Card>`,
  }),
}
