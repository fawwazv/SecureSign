import { apiClient } from '@/services/apiClient'
import type { Paginated } from '@/types/api'

/**
 * Tipe lokal FE2 (cermin openapi.yaml, tanpa menyentuh src/types/api.ts milik FE1).
 * Diselaraskan dengan docs/api-docs/openapi.yaml v0.1.
 */
export type DocumentStatus = 'DRAFT' | 'PENDING' | 'SIGNED' | 'REJECTED'
export type SignRequestStatus = 'PENDING' | 'APPROVED' | 'REJECTED'

export interface DocumentItem {
  id: string
  title: string
  description?: string | null
  storagePath: string
  fileHash: string
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  metadata: Record<string, any>
  status: DocumentStatus
  version: number
  createdAt: string
  updatedAt: string
}

export interface SignRequestItem {
  id: string
  documentId: string
  signerId: string
  status: SignRequestStatus
  message?: string | null
  rejectReason?: string | null
  createdAt: string
  updatedAt: string
}

export interface SignatureItem {
  id: string
  documentId: string
  signerId: string
  keyPairId: string
  algorithm: string
  signatureValue: string
  signedHash: string
  canonicalMetadata: string
  qrPayload: string
  signedPdfPath?: string | null
  createdAt: string
}

export interface AuditLogItem {
  id: string
  actorId?: string | null
  action: string
  entity?: string | null
  entityId?: string | null
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  details: Record<string, any>
  ipAddress?: string | null
  createdAt: string
}

export interface NotificationItem {
  id: string
  type: string
  title: string
  message: string
  isRead: boolean
  createdAt: string
}

export interface KeyPairItem {
  id: string
  algorithm: string
  publicKey: string
  revoked: boolean
  revokedAt?: string | null
  createdAt: string
}

export interface BatchApproveEntry {
  signRequestId: string
  keyPairId: string
}

export interface BatchApproveResult {
  signRequestId: string
  success: boolean
  signatureId?: string | null
  error?: { code: string; message: string } | null
}

const MAX_PDF_BYTES = 25 * 1024 * 1024

export function assertPdfFile(file: File): void {
  if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
    throw new Error('File harus berformat PDF.')
  }
  if (file.size > MAX_PDF_BYTES) {
    throw new Error('Ukuran PDF melebihi 25 MB.')
  }
}

/** Service dokumen FE2: tipis di atas apiClient FE1 (interceptor JWT + redirect 401 dipakai ulang). */
export const documentService = {
  async listDocuments(params: { page?: number; limit?: number; status?: DocumentStatus | '' } = {}) {
    const { data } = await apiClient.get<Paginated<DocumentItem> | { data: DocumentItem[]; page: number; limit: number; total: number }>('/documents', {
      params: {
        page: params.page ?? 1,
        limit: params.limit ?? 20,
        ...(params.status ? { status: params.status } : {}),
      },
    })
    return data
  },

  async getDocument(id: string) {
    const { data } = await apiClient.get<DocumentItem>(`/documents/${id}`)
    return data
  },

  async uploadDocument(input: { file: File; title: string; description?: string; metadata?: string }) {
    assertPdfFile(input.file)
    const form = new FormData()
    form.append('file', input.file)
    form.append('title', input.title)
    if (input.description) form.append('description', input.description)
    if (input.metadata) form.append('metadata', input.metadata)
    const { data } = await apiClient.post<DocumentItem>('/documents', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  async requestSign(documentId: string, payload: { signerId: string; message?: string }) {
    const { data } = await apiClient.post<SignRequestItem>(`/documents/${documentId}/request-sign`, payload)
    return data
  },

  async listPendingSignRequests(params: { page?: number; limit?: number } = {}) {
    const { data } = await apiClient.get<{ data: SignRequestItem[]; page: number; limit: number; total: number }>('/sign-requests/pending', {
      params: { page: params.page ?? 1, limit: params.limit ?? 20 },
    })
    return data
  },

  async approveSignRequest(id: string, keyPairId: string) {
    const { data } = await apiClient.post<SignatureItem>(`/sign-requests/${id}/approve`, { keyPairId })
    return data
  },

  async batchApprove(items: BatchApproveEntry[]) {
    const { data } = await apiClient.post<{ results: BatchApproveResult[] }>('/sign-requests/batch-approve', { items })
    return data
  },

  async rejectSignRequest(id: string, rejectReason: string) {
    if (!rejectReason.trim()) throw new Error('Alasan penolakan wajib diisi.')
    const { data } = await apiClient.post<SignRequestItem>(`/sign-requests/${id}/reject`, { rejectReason })
    return data
  },

  async listAuditLogs(params: { page?: number; limit?: number } = {}) {
    const { data } = await apiClient.get<{ data: AuditLogItem[]; page: number; limit: number; total: number }>('/audit-logs', {
      params: { page: params.page ?? 1, limit: params.limit ?? 20 },
    })
    return data
  },

  async listNotifications(params: { page?: number; limit?: number } = {}) {
    const { data } = await apiClient.get<{ data: NotificationItem[]; page: number; limit: number; total: number }>('/notifications', {
      params: { page: params.page ?? 1, limit: params.limit ?? 20 },
    })
    return data
  },

  async listKeys() {
    const { data } = await apiClient.get<{ data: KeyPairItem[] }>('/keys')
    return data
  },

  async revokeKey(id: string) {
    const { data } = await apiClient.post<KeyPairItem>(`/keys/${id}/revoke`)
    return data
  },
}
