import { computed } from 'vue'
import { useDocumentStore } from '@/stores/documentStore'

/** Composable sign-request Signer (FE2): facade tipis di atas documentStore. */
export function useSignRequest() {
  const store = useDocumentStore()

  return {
    pending: computed(() => store.pending),
    pendingTotal: computed(() => store.pendingTotal),
    pendingCount: computed(() => store.pendingCount),
    selectedIds: computed(() => store.selectedIds),
    hasSelection: computed(() => store.hasSelection),
    isLoading: computed(() => store.isLoading),
    error: computed(() => store.error),
    fetchPending: () => store.fetchPending(),
    toggleSelect: (id: string) => store.toggleSelect(id),
    clearSelection: () => store.clearSelection(),
    approve: (id: string, keyPairId: string, position?: string) => store.approve(id, keyPairId, position),
    batchApprove: (items: Array<{ signRequestId: string; keyPairId: string }>) => store.batchApprove(items),
    reject: (id: string, reason: string) => store.reject(id, reason),
    clearError: () => store.clearError(),
  }
}
