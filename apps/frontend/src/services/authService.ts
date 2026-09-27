import { apiClient } from './apiClient'
import type { AuthTokens, LoginPayload, RegisterPayload, User, VerifyResult } from '@/types/api'

export const authService = {
  async register(payload: RegisterPayload): Promise<User> {
    const { data } = await apiClient.post<User>('/auth/register', payload)
    return data
  },

  async login(payload: LoginPayload): Promise<{ user: User; tokens: AuthTokens }> {
    const { data } = await apiClient.post<{ user: User; tokens: AuthTokens }>(
      '/auth/login',
      payload,
    )
    return data
  },

  async refresh(refreshToken: string): Promise<AuthTokens> {
    const { data } = await apiClient.post<AuthTokens>('/auth/refresh', { refreshToken })
    return data
  },

  async logout(refreshToken?: string): Promise<void> {
    if (refreshToken) await apiClient.post('/auth/logout', { refreshToken }).catch(() => {})
  },

  async resendVerification(email: string): Promise<void> {
    await apiClient.post('/auth/resend-verification', { email })
  },

  async forgotPassword(email: string): Promise<void> {
    await apiClient.post('/auth/forgot-password', { email })
  },

  async me(): Promise<User> {
    const { data } = await apiClient.get<User>('/auth/me')
    return data
  },
}

export const verifyService = {
  /** Verifikasi publik tanpa login (F-13): upload PDF atau payload QR. */
  async verifyPublic(file: File): Promise<VerifyResult> {
    const form = new FormData()
    form.append('file', file)
    const { data } = await apiClient.post<VerifyResult>('/verify', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  async verifyByToken(token: string): Promise<VerifyResult> {
    const { data } = await apiClient.get<VerifyResult>(`/verify/${encodeURIComponent(token)}`)
    return data
  },
}
