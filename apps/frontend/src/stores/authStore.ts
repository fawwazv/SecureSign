import { defineStore } from 'pinia'
import { authService } from '@/services/authService'
import { toApiCode, toApiMessage } from '@/services/apiClient'
import { useJWT } from '@/composables/useJWT'
import { completeProfileErrorMessage, loginErrorMessage } from '@/utils/validators'
import type { CompleteProfilePayload, LoginResponse, RegisterPayload, User } from '@/types/api'

interface AuthState {
  user: User | null
  profileCompleted: boolean | null
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
  state: (): AuthState => {
    const cachedUser = readUser()
    return {
      user: cachedUser,
      profileCompleted: cachedUser?.profileCompleted ?? null,
      isLoading: false,
      error: null,
    }
  },

  getters: {
    isAuthenticated: (s) => !!s.user,
    role: (s) => s.user?.role ?? null,
    /** FE1-4: state onboarding eksplisit; null berarti flag belum tersedia (user lama). */
    needsOnboarding: (s): boolean => !!s.user && s.profileCompleted === false,
  },

  actions: {
    clearError() {
      this.error = null
    },

    roleHome(): string {
      if (this.needsOnboarding) return '/onboarding'
      switch (this.user?.role) {
        case 'SUPER_ADMIN':
          return '/admin'
        case 'SEKRETARIAT':
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
        // Samakan dengan Google: user BE kini membawa profileCompleted.
        // LoginResponse.user bertipe generated lama -> cast ke User FE1-2.
        if ((resp.user as User).profileCompleted === undefined) {
          try {
            const me = await authService.me()
            if (me && (me as User).id) resp.user = me
          } catch {
            /* abaikan, pakai user dari login */
          }
        }
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

    /** FE1-4: login Google — simpan sesi + kembalikan flag onboarding. */
    async loginWithGoogle(idToken: string) {
      this.isLoading = true
      this.error = null
      try {
        const resp = await authService.loginWithGoogle({ idToken })
        this.hydrateFromLoginResponse({ user: resp.user, tokens: resp.tokens })
        // Sinkronkan flag BE (response Google membawa profileCompleted terpisah).
        this.profileCompleted = resp.profileCompleted
        if (this.user) {
          this.user = { ...this.user, profileCompleted: resp.profileCompleted }
          try {
            localStorage.setItem('sv:user', JSON.stringify(this.user))
          } catch {
            /* abaikan */
          }
        }
        return { user: this.user as User, needsOnboarding: this.needsOnboarding }
      } catch (e) {
        const code = toApiCode(e)
        this.error = loginErrorMessage(code, toApiMessage(e, 'Login Google gagal. Coba lagi.'))
        throw e
      } finally {
        this.isLoading = false
      }
    },

    /** FE1-4: onboarding — PATCH profil lalu update user lokal. */
    async completeProfile(payload: CompleteProfilePayload): Promise<User> {
      this.isLoading = true
      this.error = null
      try {
        const user = await authService.completeProfile(payload)
        this.user = { ...user, profileCompleted: true }
        this.profileCompleted = true
        try {
          localStorage.setItem('sv:user', JSON.stringify(this.user))
        } catch {
          /* abaikan */
        }
        // Token lama masih membawa role lama -> refresh agar klaim role baru.
        // Gagal refresh = paksa login ulang, jangan biarkan 403 diam-diam.
        try {
          const rt = localStorage.getItem('sv:refresh_token') ?? undefined
          if (!rt) throw new Error('no-refresh-token')
          const refreshed = await authService.refresh(rt)
          this.hydrateFromLoginResponse(refreshed)
          this.user = { ...(this.user as User), profileCompleted: true }
          this.profileCompleted = true
          try {
            localStorage.setItem('sv:user', JSON.stringify(this.user))
          } catch {
            /* abaikan */
          }
        } catch {
          await this.logout()
          throw new Error('Sesi diperbarui, silakan masuk kembali.')
        }
        return this.user as User
      } catch (e) {
        const code = toApiCode(e)
        if (e instanceof Error && e.message === 'Sesi diperbarui, silakan masuk kembali.') {
          this.error = e.message
        } else {
          this.error = completeProfileErrorMessage(code, toApiMessage(e, 'Penyimpanan profil gagal. Coba lagi.'))
        }
        throw e
      } finally {
        this.isLoading = false
      }
    },

    /** Simpan pasangan token rotasi BE + profil ke storage lokal. */
    hydrateFromLoginResponse(resp: LoginResponse) {
      const { setTokens } = useJWT()
      setTokens(resp.tokens.accessToken, resp.tokens.refreshToken)
      const user = resp.user as User
      this.user = user
      this.profileCompleted = user.profileCompleted ?? null
      try {
        localStorage.setItem('sv:user', JSON.stringify(user))
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
        localStorage.removeItem('sv:google_credential')
        this.user = null
        this.profileCompleted = null
      }
    },
  },
})
