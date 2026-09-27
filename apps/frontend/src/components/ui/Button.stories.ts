import type { Meta, StoryObj } from '@storybook/vue3'
import Button from './Button.vue'

const meta: Meta<typeof Button> = {
  title: 'UI/Button',
  component: Button,
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'accent', 'ghost', 'danger', 'outline'],
    },
    size: { control: 'select', options: ['sm', 'md', 'lg'] },
  },
}

export default meta
type Story = StoryObj<typeof Button>

function tpl(label: string): Story['render'] {
  return (args) => ({
    components: { Button },
    setup: () => ({ args }),
    template: `<Button v-bind="args">${label}</Button>`,
  })
}

export const Primary: Story = { args: { variant: 'primary' }, render: tpl('Simpan') }
export const Secondary: Story = { args: { variant: 'secondary' }, render: tpl('Verifikasi') }
export const Accent: Story = { args: { variant: 'accent' }, render: tpl('Daftar') }
export const Ghost: Story = { args: { variant: 'ghost' }, render: tpl('Masuk') }
export const Danger: Story = { args: { variant: 'danger' }, render: tpl('Hapus') }
export const Loading: Story = { args: { variant: 'primary', loading: true }, render: tpl('Memproses…') }
export const Disabled: Story = { args: { variant: 'primary', disabled: true }, render: tpl('Nonaktif') }
export const Large: Story = { args: { variant: 'primary', size: 'lg' }, render: tpl('Mulai Gratis') }
