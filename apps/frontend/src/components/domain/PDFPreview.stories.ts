import type { Meta, StoryObj } from '@storybook/vue3'
import PDFPreview from './PDFPreview.vue'

const meta: Meta<typeof PDFPreview> = {
  title: 'Domain/PDFPreview',
  component: PDFPreview,
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof PDFPreview>

export const Default: Story = {
  args: { src: '/contoh-dokumen.pdf', title: 'Kontrak Kerja Sama 2026' },
}
