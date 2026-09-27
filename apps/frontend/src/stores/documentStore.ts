import { defineStore } from 'pinia'
import { toApiMessage } from '@/services/apiClient'
import {
  documentService,
  type AuditLogItem,
  type BatchApproveEntry,
  type DocumentItem,
  type DocumentStatus,
  type NotificationItem,
  type SignRequestItem,
} from '@/services/documentService'

interface DocumentState {
  documents: DocumentItem[]
  documentsPage: number
  documentsLimit: number
  documentsTotal: number
  statusFilter: DocumentStatus | ''
  pending: SignRequestItem[]
  pendingPage: number
  pendingLimit: number
  pendingTotal: number
  auditLogs: AuditLogItem[]
  auditPage: number
  auditLimit: number
  auditTotal: number
  notifications: NotificationItem[]
  selectedIds: string[]
  isLoading: boolean
  error: string | null
}

export const useDocumentStore = defineStore('document', {
  state: (): DocumentState => ({
    documents: [],
    documentsPage: 1,
    documentsLimit: 20,
    documentsTotal: 0,
    statusFilter: '',
    pending: [],
    pendingPage: 1,
    pendingLimit: 20,
    pendingTotal: 0,
    auditLogs: [],
    auditPage: 1,
    auditLimit: 20,
    auditTotal: 0,
    notifications: [],
    selectedIds: [],
    isLoading: false,
    error: null,
  }),

  getters: {
    pendingCount: (s) => s.pendingTotal,
    hasSelection: (s) => s.selectedIds.length > 0,
  },

  actions: {
    clearError() {
      this.error = null
    },

    setStatusFilter(status: DocumentStatus | '') {
      this.statusFilter = status
      this.documentsPage = 1
    },

    toggleSelect(id: string) {
      this.selectedIds = this.selectedIds.includes(id)
        ? this.selectedIds.filter((x) => x !== id)
        : [...this.selectedIds, id]
    },

    clearSelection() {
      this.selectedIds = []
    },

    async fetchDocuments() {
      this.isLoading = true
      this.error = null
      try {
        const res = await documentService.listDocuments({
          page: this.documentsPage,
          limit: this.documentsLimit,
          status: this.statusFilter,
        })
        this.documents = res.data
        this.documentsPage = res.page
        this.documentsLimit = res.limit
        this.documentsTotal = res.total
      } catch (e) {
        this.error = toApiMessage(e, 'Gagal memuat dokumen.')
        throw e
      } finally {
        this.isLoading = false
      }
    },

    async uploadDocument(input: { file: File; title: string; description?: string; metadata?: string }) {
      this.isLoading = true
      this.error = null
      try {
        const doc = await documentService.uploadDocument(input)
        await this.fetchDocuments()
        return doc
      } catch (e) {
        this.error = toApiMessage(e, 'Upload PDF gagal.')
        throw e
      } finally {
        this.isLoading = false
      }
    },

    async requestSign(documentId: string, payload: { signerId: string; message?: string }) {
      this.isLoading = true
      this.error = null
      try {
        const req = await documentService.requestSign(documentId, payload)
        await this.fetchDocuments()
        return req
      } catch (e) {
        this.error = toApiMessage(e, 'Request tanda tangan gagal.')
        throw e
      } finally {
        this.isLoading = false
      }
    },

    async fetchPending() {
      this.isLoading = true
      this.error = null
      try {
        const res = await documentService.listPendingSignRequests({
          page: this.pendingPage,
          limit: this.pendingLimit,
        })
        this.pending = res.data
        this.pendingPage = res.page
        this.pendingLimit = res.limit
        this.pendingTotal = res.total
      } catch (e) {
        this.error = toApiMessage(e, 'Gagal memuat antrean tanda tangan.')
        throw e
      } finally {
        this.isLoading = false
      }
    },

    async approve(id: string, keyPairId: string) {
      this.isLoading = true
      this.error = null
      try {
        const sig = await documentService.approveSignRequest(id, keyPairId)
        this.selectedIds = this.selectedIds.filter((x) => x !== id)
        await this.fetchPending()
        return sig
      } catch (e) {
        this.error = toApiMessage(e, 'Tanda tangan gagal.')
        throw e
      } finally {
        this.isLoading = false
      }
    },

    async batchApprove(items: BatchApproveEntry[]) {
      this.isLoading = true
      this.error = null
      try {
        const res = await documentService.batchApprove(items)
        this.clearSelection()
        await this.fetchPending()
        return res
      } catch (e) {
        this.error = toApiMessage(e, 'Batch signing gagal.')
        throw e
      } finally {
        this.isLoading = false
      }
    },

    async reject(id: string, reason: string) {
      this.isLoading = true
      this.error = null
      try {
        const req = await documentService.rejectSignRequest(id, reason)
        this.selectedIds = this.selectedIds.filter((x) => x !== id)
        await this.fetchPending()
        return req
      } catch (e) {
        this.error = toApiMessage(e, 'Penolakan gagal.')
        throw e
      } finally {
        this.isLoading = false
      }
    },

    async fetchAuditLogs() {
      this.isLoading = true
      this.error = null
      try {
        const res = await documentService.listAuditLogs({ page: this.auditPage, limit: this.auditLimit })
        this.auditLogs = res.data
        this.auditPage = res.page
        this.auditLimit = res.limit
        this.auditTotal = res.total
      } catch (e) {
        this.error = toApiMessage(e, 'Gagal memuat audit log.')
        throw e
      } finally {
        this.isLoading = false
      }
    },

    async fetchNotifications() {
      try {
        const res = await documentService.listNotifications({ page: 1, limit: 20 })
        this.notifications = res.data
      } catch {
        this.notifications = []
      }
    },
  },
})
