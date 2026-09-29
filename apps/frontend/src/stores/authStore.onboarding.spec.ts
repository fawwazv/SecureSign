import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '@/stores/authStore'
import { authService } from '@/services/authService'
import type { CompleteProfilePayload, GoogleLoginResponse, LoginResponse, User } from '@/types/api'

vi.mock('@/services/authService', () => ({
  authService: {
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    refresh: vi.fn(),
    verifyEmail: vi.fn(),
    resendVerification: vi.fn(),
    me: vi.fn(),
    loginWithGoogle: vi.fn(),
    completeProfile: vi.fn(),
  },
}))

const mockedComplete = vi.mocked(authService.completeProfile)
const mockedRefresh = vi.mocked(authService.refresh)

function tokens(acc: string, ref: string): LoginResponse['tokens'] {
  return { accessToken: acc, refreshToken: ref, expiresIn: 900 }
}

function user(over: Partial<User> = {}): User {
  return {
    id: 'u-9',
    fullName: 'Sinta',
    email: 'sinta@pt.id',
    organization: '',
    role: 'SIGNER',
    emailVerified: true,
    profileCompleted: false,
    ...over,
  } as User
}

const payload: CompleteProfilePayload = {
  fullName: 'Sinta',
  organization: 'PT Maju',
  phone: '+628123456789',
  role: 'SEKRETARIAT',
  purpose: 'kerja',
}

describe('completeProfile me-refresh token (anti token basi)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
    localStorage.setItem('sv:refresh_token', 'ref-lama')
  })

  it('sukses PATCH -> refresh terpanggil -> token baru tersimpan', async () => {
    mockedComplete.mockResolvedValue(user({ role: 'SEKRETARIAT' }))
    const refreshed: LoginResponse = {
      user: user({ role: 'SEKRETARIAT', organization: 'PT Maju', profileCompleted: true }),
      tokens: tokens('acc-baru', 'ref-baru'),
    }
    mockedRefresh.mockResolvedValue(refreshed)
    const store = useAuthStore()
    const out = await store.completeProfile(payload)
    expect(mockedRefresh).toHaveBeenCalledWith('ref-lama')
    expect(out.role).toBe('SEKRETARIAT')
    expect(localStorage.getItem('sv:access_token')).toBe('acc-baru')
    expect(store.profileCompleted).toBe(true)
  })

  it('refresh gagal -> paksa logout, tidak macet 403 diam-diam', async () => {
    mockedComplete.mockResolvedValue(user({ role: 'SEKRETARIAT' }))
    mockedRefresh.mockRejectedValue(new Error('jaringan putus'))
    const store = useAuthStore()
    await expect(store.completeProfile(payload)).rejects.toThrow('Sesi diperbarui')
    expect(store.user).toBeNull()
    expect(store.error).toContain('masuk kembali')
  })

  it('loginWithGoogle membawa flag onboarding dari response', async () => {
    const mockedG = vi.mocked(authService.loginWithGoogle)
    const resp: GoogleLoginResponse = {
      user: user(),
      tokens: tokens('acc-g', 'ref-g'),
      profileCompleted: false,
    }
    mockedG.mockResolvedValue(resp)
    const store = useAuthStore()
    const out = await store.loginWithGoogle('id-token')
    expect(out.needsOnboarding).toBe(true)
    expect(store.roleHome()).toBe('/onboarding')
  })
})
