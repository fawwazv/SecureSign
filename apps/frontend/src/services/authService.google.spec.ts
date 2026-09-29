import { describe, expect, it, vi, beforeEach } from 'vitest'
import { apiClient } from '@/services/apiClient'
import { authService } from '@/services/authService'

vi.mock('@/services/apiClient', () => ({
  apiClient: { post: vi.fn(), patch: vi.fn(), get: vi.fn() },
}))

const post = apiClient.post as unknown as ReturnType<typeof vi.fn>
const patch = apiClient.patch as unknown as ReturnType<typeof vi.fn>

beforeEach(() => {
  vi.clearAllMocks()
})

describe('authService Google + onboarding (FE1-3)', () => {
  it('loginWithGoogle POST /auth/google {idToken}', async () => {
    const fake = {
      user: { id: 'u1', profileCompleted: false },
      tokens: { accessToken: 'a', refreshToken: 'r', expiresIn: 900 },
      profileCompleted: false,
    }
    post.mockResolvedValue({ data: fake })
    const res = await authService.loginWithGoogle({ idToken: 'tok123' })
    expect(post).toHaveBeenCalledWith('/auth/google', { idToken: 'tok123' })
    expect(res.profileCompleted).toBe(false)
  })

  it('completeProfile PATCH /users/me/complete-profile', async () => {
    const fakeUser = { id: 'u1', profileCompleted: true }
    patch.mockResolvedValue({ data: fakeUser })
    const payload = {
      fullName: 'Sinta Prabowo',
      organization: 'PT Maju Jaya',
      phone: '+628123456789',
      role: 'SEKRETARIAT' as const,
      purpose: 'TTD kontrak vendor',
    }
    const res = await authService.completeProfile(payload)
    expect(patch).toHaveBeenCalledWith('/users/me/complete-profile', payload)
    expect(res.profileCompleted).toBe(true)
  })

  it('register meneruskan phone + captchaToken', async () => {
    const postMock = post as unknown as ReturnType<typeof vi.fn>
    postMock.mockResolvedValue({ data: { id: 'u2' } })
    await authService.register({
      fullName: 'Tes',
      email: 't@example.com',
      password: 'Rahasia123',
      organization: 'PT Tes',
      role: 'SIGNER',
      purpose: 'testing',
      phone: '+62811',
      captchaToken: 'cap-tok',
    })
    expect(postMock).toHaveBeenCalledWith(
      '/auth/register',
      expect.objectContaining({ phone: '+62811', captchaToken: 'cap-tok' }),
    )
  })
})
