import type { Meta, StoryObj } from '@storybook/vue3'
import Input from './Input.vue'

const meta: Meta<typeof Input> = {
  title: 'UI/Input',
  component: Input,
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof Input>

export const Default: Story = {
  args: { id: 'email', label: 'Email', placeholder: 'nama@perusahaan.id' },
  render: (args) => ({
    components: { Input },
    setup: () => ({ args }),
    template: '<Input v-bind="args" v-model="args.modelValue" />',
  }),
}

export const WithError: Story = {
  args: { id: 'email', label: 'Email', modelValue: 'bukan-email', error: 'Format email tidak valid.' },
  render: (args) => ({
    components: { Input },
    setup: () => ({ args }),
    template: '<Input v-bind="args" v-model="args.modelValue" />',
  }),
}

export const WithHint: Story = {
  args: {
    id: 'password',
    label: 'Kata sandi',
    type: 'password',
    modelValue: '',
    hint: 'Disimpan sebagai hash Argon2id di server.',
  },
  render: (args) => ({
    components: { Input },
    setup: () => ({ args }),
    template: '<Input v-bind="args" v-model="args.modelValue" />',
  }),
}
