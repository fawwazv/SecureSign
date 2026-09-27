import type { Meta, StoryObj } from '@storybook/vue3'
import NotificationDropdown from './NotificationDropdown.vue'

const meta: Meta<typeof NotificationDropdown> = {
  title: 'Domain/NotificationDropdown',
  component: NotificationDropdown,
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof NotificationDropdown>

export const WithItems: Story = {
  args: {
    items: [
      { id: 'n1', title: 'Permintaan baru', message: 'doc-001 menunggu tanda tangan', read: false },
      { id: 'n2', title: 'Dokumen ditandatangani', message: 'doc-002 selesai', read: true },
    ],
  },
}

export const Empty: Story = { args: { items: [] } }
