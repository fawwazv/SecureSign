import type { Meta, StoryObj } from '@storybook/vue3'
import QRViewer from './QRViewer.vue'

const meta: Meta<typeof QRViewer> = {
  title: 'Domain/QRViewer',
  component: QRViewer,
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof QRViewer>

export const Default: Story = {
  args: { qrPayload: 'http://localhost:8000/api/v1/verify/sig-abc123' },
}
