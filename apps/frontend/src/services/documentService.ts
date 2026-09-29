import { apiClient } from '@/services/apiClient'
import type { Paginated, Role } from '@/types/api'

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
  pageCount: number
  qrPlacements: { page: number; x: number; y: number; size: number }[]
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

/**
 * Unduh PDF asli / bertanda tangan sebagai Blob (auth via interceptor).
 * Iframe tidak bisa membawa header Authorization, jadi unduhan lewat
 * apiClient lalu dibuat object URL — file tetap privat, tanpa token di URL.
 */
export async function downloadDocumentBlob(
  documentId: string,
  kind: 'original' | 'signed' = 'original',
): Promise<Blob> {
  const { data } = await apiClient.get<Blob>(`/documents/${documentId}/download`, {
    params: { kind },
    responseType: 'blob',
  })
  return data
}

/** Simpan posisi QR (fraksi 0..1). Hanya pemilik + DRAFT. */
export async function saveQrPlacements(
  documentId: string,
  placements: { page: number; x: number; y: number; size: number }[],
) {
  const { data } = await apiClient.put(`/documents/${documentId}/qr-placements`, { placements })
  return data
}

/** Daftar user untuk dropdown (mis. pilih Signer). Butuh Org Admin / Super Admin. */
export async function listUsers(params: { role?: string; page?: number; limit?: number } = {}) {
  const { data } = await apiClient.get<
    Paginated<{ id: string; fullName: string; email: string; organization: string; role: Role }>
  >('/users', {
    params: { page: params.page ?? 1, limit: params.limit ?? 100, ...(params.role ? { role: params.role } : {}) },
  })
  return data
}

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

  async generateKeyPair(algorithm: 'RSA_PSS_2048' | 'ECDSA_P256' | 'ED25519') {
    const { data } = await apiClient.post<KeyPairItem>('/keys/generate', { algorithm })
    return data
  },

  async revokeKey(id: string) {
    const { data } = await apiClient.post<KeyPairItem>(`/keys/${id}/revoke`)
    return data
  },
}
