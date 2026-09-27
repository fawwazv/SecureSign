import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { AxiosError, AxiosHeaders } from 'axios'
import { useAuthStore } from '@/stores/authStore'
import { authService } from '@/services/authService'
import type { ApiErrorBody, LoginResponse } from '@/types/api'

vi.mock('@/services/authService', () => ({
  authService: {
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    refresh: vi.fn(),
    verifyEmail: vi.fn(),
    resendVerification: vi.fn(),
    me: vi.fn(),
  },
}))

const mockedLogin = vi.mocked(authService.login)

const resp: LoginResponse = {
  user: {
    id: 'u-1',
    fullName: 'Sinta Prabowo',
    email: 'sinta@pt.id',
    organization: 'PT Maju',
    role: 'ORG_ADMIN',
    emailVerified: true,
    createdAt: '2026-09-27T10:00:00Z',
  },
  tokens: { accessToken: 'acc', refreshToken: 'ref', expiresIn: 900 },
}

function apiError(code: string, message: string, status: number): AxiosError<ApiErrorBody> {
  const err = new AxiosError<ApiErrorBody>(message)
  err.response = {
    data: { error: { code, message } },
    status,
    statusText: 'err',
    headers: {},
    config: { headers: new AxiosHeaders() },
  }
  return err
}

describe('authStore ↔ authService (kontrak BE)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('login sukses menyimpan user + pasangan token rotasi', async () => {
    mockedLogin.mockResolvedValue(resp)
    const store = useAuthStore()
    const user = await store.login('sinta@pt.id', 'Rahasia123')
    expect(user.email).toBe('sinta@pt.id')
    expect(store.isAuthenticated).toBe(true)
    expect(localStorage.getItem('sv:access_token')).toBe('acc')
    expect(localStorage.getItem('sv:refresh_token')).toBe('ref')
  })

  it('401 INVALID_CREDENTIALS menampilkan pesan Ramah', async () => {
    mockedLogin.mockRejectedValue(apiError('INVALID_CREDENTIALS', 'Email atau kata sandi salah.', 401))
    const store = useAuthStore()
    await expect(store.login('a@b.id', 'salah')).rejects.toThrow()
    expect(store.user).toBeNull()
    expect(store.error).toContain('salah')
  })

  it('403 EMAIL_NOT_VERIFIED memberi pesan verifikasi (halaman akan redirect)', async () => {
    mockedLogin.mockRejectedValue(apiError('EMAIL_NOT_VERIFIED', 'Email belum terverifikasi.', 403))
    const store = useAuthStore()
    await expect(store.login('baru@pt.id', 'Rahasia123')).rejects.toThrow()
    expect(store.error).toContain('belum terverifikasi')
  })
})
