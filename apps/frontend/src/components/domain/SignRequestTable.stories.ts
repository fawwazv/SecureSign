import type { Meta, StoryObj } from '@storybook/vue3'
import SignRequestTable from './SignRequestTable.vue'
import type { SignRequestItem } from '@/services/documentService'

const rows: SignRequestItem[] = [
  {
    id: 'req-001',
    documentId: 'doc-001',
    signerId: 'signer-1',
    status: 'PENDING',
    message: 'Mohon review & tanda tangani.',
    rejectReason: null,
    createdAt: '2026-09-27T10:00:00Z',
    updatedAt: '2026-09-27T10:00:00Z',
  },
  {
    id: 'req-002',
    documentId: 'doc-002',
    signerId: 'signer-1',
    status: 'APPROVED',
    message: null,
    rejectReason: null,
    createdAt: '2026-09-26T10:00:00Z',
    updatedAt: '2026-09-26T12:00:00Z',
  },
]

const meta: Meta<typeof SignRequestTable> = {
  title: 'Domain/SignRequestTable',
  component: SignRequestTable,
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof SignRequestTable>

export const Readonly: Story = { args: { rows } }
export const Selectable: Story = { args: { rows, selectable: true, selectedIds: ['req-001'] } }
export const Empty: Story = { args: { rows: [] } }
