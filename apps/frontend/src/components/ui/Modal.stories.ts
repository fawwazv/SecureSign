import type { Meta, StoryObj } from '@storybook/vue3'
import { ref } from 'vue'
import Modal from './Modal.vue'
import Button from './Button.vue'

const meta: Meta<typeof Modal> = {
  title: 'UI/Modal',
  component: Modal,
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof Modal>

export const Open: Story = {
  args: { open: true, title: 'Tolak dokumen?' },
  render: (args) => ({
    components: { Modal, Button },
    setup: () => {
      const open = ref(true)
      return { args, open }
    },
    template: `
      <div>
        <Button variant="outline" @click="open = true">Buka modal</Button>
        <Modal :open="open" title="Tolak dokumen?" @close="open = false">
          <p class="text-sm text-slate-600">Tulis alasan penolakan untuk audit trail.</p>
          <div class="mt-4 flex justify-end gap-2">
            <Button variant="ghost" size="sm" @click="open = false">Batal</Button>
            <Button variant="danger" size="sm" @click="open = false">Tolak</Button>
          </div>
        </Modal>
      </div>`,
  }),
}
