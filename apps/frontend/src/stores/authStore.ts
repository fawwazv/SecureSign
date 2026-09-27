import { defineStore } from 'pinia'
import { authService } from '@/services/authService'
import { toApiCode, toApiMessage } from '@/services/apiClient'
import { useJWT } from '@/composables/useJWT'
import { loginErrorMessage } from '@/utils/validators'
import type { LoginResponse, RegisterPayload, User } from '@/types/api'

interface AuthState {
  user: User | null
  isLoading: boolean
  error: string | null
}

function readUser(): User | null {
  try {
    const raw = localStorage.getItem('sv:user')
    return raw ? (JSON.parse(raw) as User) : null
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: readUser(),
    isLoading: false,
    error: null,
  }),

  getters: {
    isAuthenticated: (s) => !!s.user,
    role: (s) => s.user?.role ?? null,
  },

  actions: {
    clearError() {
      this.error = null
    },

    roleHome(): string {
      switch (this.user?.role) {
        case 'SUPER_ADMIN':
          return '/admin'
        case 'ORG_ADMIN':
          return '/org'
        case 'SIGNER':
          return '/signer'
        default:
          return '/'
      }
    },

    async register(payload: RegisterPayload): Promise<User> {
      this.isLoading = true
      this.error = null
      try {
        return await authService.register(payload)
      } catch (e) {
        this.error = toApiMessage(e, 'Registrasi gagal. Coba lagi.')
        throw e
      } finally {
        this.isLoading = false
      }
    },

    async login(email: string, password: string) {
      this.isLoading = true
      this.error = null
      try {
        const resp = await authService.login({ email, password })
        this.hydrateFromLoginResponse(resp)
        return resp.user
      } catch (e) {
        const code = toApiCode(e)
        this.error = loginErrorMessage(code, toApiMessage(e, 'Email atau kata sandi salah.'))
        throw e
      } finally {
        this.isLoading = false
      }
    },

    /** Simpan pasangan token rotasi BE + profil ke storage lokal. */
    hydrateFromLoginResponse(resp: LoginResponse) {
      const { setTokens } = useJWT()
      setTokens(resp.tokens.accessToken, resp.tokens.refreshToken)
      this.user = resp.user
      try {
        localStorage.setItem('sv:user', JSON.stringify(resp.user))
      } catch {
        /* abaikan */
      }
    },

    async logout() {
      try {
        await authService.logout(localStorage.getItem('sv:refresh_token') ?? undefined)
      } finally {
        const { clearTokens } = useJWT()
        clearTokens()
        localStorage.removeItem('sv:user')
        this.user = null
      }
    },
  },
})
