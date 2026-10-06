import { apiClient } from './apiClient'
import type {
  AuthTokens,
  CompleteProfilePayload,
  GoogleLoginPayload,
  GoogleLoginResponse,
  LoginPayload,
  LoginResponse,
  RegisterPayload,
  User,
  VerifyEmailPayload,
  VerifyResult,
} from '@/types/api'

export const authService = {
  async register(payload: RegisterPayload): Promise<User> {
    const { data } = await apiClient.post<User>('/auth/register', payload)
    return data
  },

  /** FE1-3: login Google — POST /auth/google {idToken} -> {user, tokens, profileCompleted}. */
  async loginWithGoogle(payload: GoogleLoginPayload): Promise<GoogleLoginResponse> {
    const { data } = await apiClient.post<GoogleLoginResponse>('/auth/google', payload)
    return data
  },

  /** FE1-3: onboarding — PATCH /users/me/complete-profile (Bearer). */
  async completeProfile(payload: CompleteProfilePayload): Promise<User> {
    const { data } = await apiClient.patch<User>('/users/me/complete-profile', payload)
    return data
  },

  /** POST /auth/verify-email {email, token} — token sekali pakai, expired 24 jam. */
  async verifyEmail(payload: VerifyEmailPayload): Promise<string> {
    const { data } = await apiClient.post<{ message: string }>('/auth/verify-email', payload)
    return data.message
  },

  async login(payload: LoginPayload): Promise<LoginResponse> {
    const { data } = await apiClient.post<LoginResponse>('/auth/login', payload)
    return data
  },

  /** BE me-rotation: response = LoginResponse {user, tokens} (bukan AuthTokens saja). */
  async refresh(refreshToken: string): Promise<LoginResponse> {
    const { data } = await apiClient.post<LoginResponse>('/auth/refresh', { refreshToken })
    return data
  },

  async logout(refreshToken?: string): Promise<void> {
    if (refreshToken) await apiClient.post('/auth/logout', { refreshToken }).catch(() => {})
  },

  async resendVerification(email: string, captchaToken?: string): Promise<string> {
    const { data } = await apiClient.post<{ message: string }>('/auth/resend-verification', {
      email,
      ...(captchaToken ? { captchaToken } : {}),
    })
    return data.message
  },

  /**
   * Endpoint lupa-password TIDAK ada di kontrak BE (disengaja, ikut PRD ketat).
   * Fungsi dipertahankan agar import halaman tidak rusak; selalu menolak
   * dengan kode FEATURE_UNAVAILABLE. Halaman terkait dinonaktifkan di Fase 3.
   */
  async forgotPassword(_email: string): Promise<never> {
    void _email
    return Promise.reject({ code: 'FEATURE_UNAVAILABLE' })
  },

  async me(): Promise<User> {
    const { data } = await apiClient.get<User>('/users/me')
    return data
  },
}

export type { AuthTokens }

export const verifyService = {
  /** Verifikasi publik tanpa login (F-13): upload PDF ke POST /verify/upload. */
  async verifyPublic(file: File): Promise<VerifyResult> {
    const form = new FormData()
    form.append('file', file)
    const { data } = await apiClient.post<VerifyResult>('/verify/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  /** Verifikasi publik via QR/link: GET /verify/{sig_id} tanpa login. */
  async verifyByToken(sigId: string): Promise<VerifyResult> {
    const { data } = await apiClient.get<VerifyResult>(`/verify/${encodeURIComponent(sigId)}`)
    return data
  },

  /** Verifikasi publik memakai file bertanda + kunci tempelan: POST /verify/manual-file. */
  async verifyManualFile(file: File, publicKey: string): Promise<VerifyResult> {
    if (file.size > 25 * 1024 * 1024) throw new Error('Ukuran file melebihi 25 MB.')
    if (!publicKey.includes('BEGIN PUBLIC KEY')) throw new Error('Kunci publik harus format PEM.')
    const form = new FormData()
    form.append('file', file)
    form.append('publicKey', publicKey.trim())
    const { data } = await apiClient.post<VerifyResult>('/verify/manual-file', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },
}
