import type { Meta, StoryObj } from '@storybook/vue3'
import Badge from './Badge.vue'

const meta: Meta<typeof Badge> = {
  title: 'UI/Badge',
  component: Badge,
  tags: ['autodocs'],
  argTypes: {
    tone: { control: 'select', options: ['draft', 'pending', 'signed', 'rejected', 'info', 'neutral'] },
  },
}

export default meta
type Story = StoryObj<typeof Badge>

function row(): Story['render'] {
  return (args) => ({
    components: { Badge },
    setup: () => ({ args }),
    template: `
      <div class="flex flex-wrap gap-2">
        <Badge tone="draft">DRAFT</Badge>
        <Badge tone="pending">PENDING</Badge>
        <Badge tone="signed">SIGNED</Badge>
        <Badge tone="rejected">REJECTED</Badge>
        <Badge tone="info">INFO</Badge>
        <Badge tone="neutral">NETRAL</Badge>
      </div>`,
  })
}

export const AllTones: Story = { args: { tone: 'pending' }, render: row() }
