import type { Meta, StoryObj } from '@storybook/vue3'
import DocumentCard from './DocumentCard.vue'
import type { DocumentItem } from '@/services/documentService'

const doc: DocumentItem = {
  id: 'doc-001',
  title: 'Kontrak Kerja Sama 2026',
  description: 'Kesepakatan layanan tahunan antara dua pihak.',
  storagePath: 'org-1/doc-001.pdf',
  fileHash: '9f2c4a1b7e3d4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0',
  metadata: {},
  status: 'PENDING',
  version: 1,
  pageCount: 1,
  qrPlacements: [],
  createdAt: '2026-09-27T10:00:00Z',
  updatedAt: '2026-09-27T10:00:00Z',
}

const meta: Meta<typeof DocumentCard> = {
  title: 'Domain/DocumentCard',
  component: DocumentCard,
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof DocumentCard>

export const Pending: Story = { args: { document: doc } }
export const Signed: Story = { args: { document: { ...doc, status: 'SIGNED' } } }
export const Rejected: Story = { args: { document: { ...doc, status: 'REJECTED' } } }
export const Draft: Story = { args: { document: { ...doc, status: 'DRAFT' } } }
