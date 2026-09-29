import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { AxiosError, AxiosHeaders } from 'axios'
import { useAuthStore } from '@/stores/authStore'
import { authService } from '@/services/authService'
import type { ApiErrorBody, User } from '@/types/api'
import { completeProfileErrorMessage, isPhone, loginErrorMessage } from '@/utils/validators'

vi.mock('@/services/authService', () => ({
  authService: {
    login: vi.fn(),
    loginWithGoogle: vi.fn(),
    completeProfile: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    refresh: vi.fn(),
    verifyEmail: vi.fn(),
    resendVerification: vi.fn(),
    me: vi.fn(),
  },
}))

const mockGoogle = vi.mocked(authService.loginWithGoogle)
const mockComplete = vi.mocked(authService.completeProfile)

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

describe('authStore Google + onboarding (FE1-4)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('loginWithGoogle baru -> needsOnboarding true -> roleHome /onboarding', async () => {
    mockGoogle.mockResolvedValue({
      user: {
        id: 'g1',
        fullName: 'Sinta',
        email: 'sinta@mail.id',
        organization: '',
        role: 'SIGNER',
        emailVerified: true,
        createdAt: '2026-09-28T00:00:00Z',
        authProvider: 'GOOGLE',
        profileCompleted: false,
      },
      tokens: { accessToken: 'a', refreshToken: 'r', expiresIn: 900 },
      profileCompleted: false,
    })
    const store = useAuthStore()
    const res = await store.loginWithGoogle('tok')
    expect(res.needsOnboarding).toBe(true)
    expect(store.needsOnboarding).toBe(true)
    expect(store.profileCompleted).toBe(false)
    expect(store.roleHome()).toBe('/onboarding')
  })

  it('completeProfile -> needsOnboarding false -> roleHome per role', async () => {
    mockComplete.mockResolvedValue({
      id: 'g1',
      fullName: 'Sinta',
      email: 'sinta@mail.id',
      organization: 'PT Maju',
      role: 'SEKRETARIAT',
      emailVerified: true,
      createdAt: '2026-09-28T00:00:00Z',
      phone: '+62812',
      authProvider: 'GOOGLE',
      profileCompleted: true,
    })
    // Perilaku anti token-basi: completeProfile me-refresh token agar klaim role baru.
    vi.mocked(authService.refresh).mockResolvedValue({
      user: {
        id: 'g1',
        fullName: 'Sinta',
        email: 'sinta@mail.id',
        organization: 'PT Maju',
        role: 'SEKRETARIAT',
        emailVerified: true,
        createdAt: '2026-09-28T00:00:00Z',
        phone: '+62812',
        authProvider: 'GOOGLE',
        profileCompleted: true,
      } as User,
      tokens: { accessToken: 'acc-baru', refreshToken: 'ref-baru', expiresIn: 900 },
    })
    const store = useAuthStore()
    localStorage.setItem('sv:refresh_token', 'ref-lama')
    const user = await store.completeProfile({
      fullName: 'Sinta',
      organization: 'PT Maju',
      phone: '+62812',
      role: 'SEKRETARIAT',
      purpose: 'TTD kontrak',
    })
    expect(user.profileCompleted).toBe(true)
    expect(store.needsOnboarding).toBe(false)
    expect(store.profileCompleted).toBe(true)
    expect(store.roleHome()).toBe('/org')
    expect(localStorage.getItem('sv:access_token')).toBe('acc-baru')
  })

  it('loginWithGoogle gagal memetakan pesan SSO', async () => {
    mockGoogle.mockRejectedValue(apiError('INVALID_GOOGLE_SUBJECT', 'tidak cocok', 401))
    const store = useAuthStore()
    await expect(store.loginWithGoogle('bad')).rejects.toThrow()
    expect(store.error).toContain('tidak cocok')
    expect(loginErrorMessage('GOOGLE_ACCOUNT_USE_SSO')).toContain('Google')
  })

  it('isPhone validasi nomor Indonesia', () => {
    expect(isPhone('+628123456789')).toBe(true)
    expect(isPhone('08123456789')).toBe(true)
    expect(isPhone('abc')).toBe(false)
  })

  it('PROFILE_ALREADY_COMPLETED memetakan pesan onboarding', () => {
    expect(completeProfileErrorMessage('PROFILE_ALREADY_COMPLETED')).toContain('sudah lengkap')
  })
})
