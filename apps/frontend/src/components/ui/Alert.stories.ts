import type { Meta, StoryObj } from '@storybook/vue3'
import Alert from './Alert.vue'

const meta: Meta<typeof Alert> = {
  title: 'UI/Alert',
  component: Alert,
  tags: ['autodocs'],
  argTypes: {
    variant: { control: 'select', options: ['info', 'success', 'warning', 'error'] },
  },
}

export default meta
type Story = StoryObj<typeof Alert>

function tpl(text: string): Story['render'] {
  return (args) => ({
    components: { Alert },
    setup: () => ({ args }),
    template: `<Alert v-bind="args">${text}</Alert>`,
  })
}

export const Info: Story = { args: { variant: 'info', title: 'Info' }, render: tpl('Tautan verifikasi dikirim ke email Anda.') }
export const Success: Story = { args: { variant: 'success', title: 'Berhasil' }, render: tpl('Dokumen VALID — hash & signature cocok.') }
export const Warning: Story = { args: { variant: 'warning', title: 'Perhatian' }, render: tpl('Kamera membutuhkan HTTPS atau localhost.') }
export const Error: Story = { args: { variant: 'error', title: 'Gagal' }, render: tpl('Dokumen TIDAK VALID atau gagal diverifikasi.') }
