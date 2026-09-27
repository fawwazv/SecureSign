import type { Meta, StoryObj } from '@storybook/vue3'
import Table from './Table.vue'

const meta: Meta = {
  title: 'UI/Table',
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  component: Table as any,
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj

const columns = [
  { key: 'event', label: 'Peristiwa' },
  { key: 'at', label: 'Waktu' },
  { key: 'actor', label: 'Aktor' },
]

export const AuditTrail: Story = {
  args: {
    columns,
    rows: [
      { event: 'UPLOADED', at: '27 Sep 2026, 09:00', actor: 'Org Admin' },
      { event: 'SIGNED', at: '27 Sep 2026, 10:15', actor: 'Direktur' },
      { event: 'VERIFIED', at: '27 Sep 2026, 11:02', actor: 'Publik' },
    ],
  },
  render: (args) => ({
    components: { Table },
    setup: () => ({ args }),
    template: '<Table v-bind="args" />',
  }),
}

export const Empty: Story = {
  args: { columns, rows: [] },
  render: (args) => ({
    components: { Table },
    setup: () => ({ args }),
    template: '<Table v-bind="args" />',
  }),
}
