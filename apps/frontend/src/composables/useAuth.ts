import { computed } from 'vue'
import { useAuthStore } from '@/stores/authStore'

/** Composable otentikasi (FE1): facade tipis di atas authStore untuk halaman publik. */
export function useAuth() {
  const store = useAuthStore()

  return {
    user: computed(() => store.user),
    isAuthenticated: computed(() => store.isAuthenticated),
    isLoading: computed(() => store.isLoading),
    error: computed(() => store.error),
    login: (email: string, password: string) => store.login(email, password),
    register: (payload: Parameters<typeof store.register>[0]) => store.register(payload),
    logout: () => store.logout(),
    clearError: () => store.clearError(),
    roleHome: () => store.roleHome(),
  }
}
