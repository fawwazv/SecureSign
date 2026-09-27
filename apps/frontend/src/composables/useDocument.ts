import { computed } from 'vue'
import { useDocumentStore } from '@/stores/documentStore'
import type { DocumentStatus } from '@/services/documentService'

/** Composable dokumen Org Admin (FE2): facade tipis di atas documentStore. */
export function useDocument() {
  const store = useDocumentStore()

  return {
    documents: computed(() => store.documents),
    documentsTotal: computed(() => store.documentsTotal),
    documentsPage: computed(() => store.documentsPage),
    statusFilter: computed(() => store.statusFilter),
    isLoading: computed(() => store.isLoading),
    error: computed(() => store.error),
    fetchDocuments: () => store.fetchDocuments(),
    setStatusFilter: (s: DocumentStatus | '') => store.setStatusFilter(s),
    setPage: (p: number) => {
      store.documentsPage = p
      return store.fetchDocuments()
    },
    uploadDocument: (input: { file: File; title: string; description?: string; metadata?: string }) =>
      store.uploadDocument(input),
    requestSign: (documentId: string, payload: { signerId: string; message?: string }) =>
      store.requestSign(documentId, payload),
    clearError: () => store.clearError(),
  }
}
