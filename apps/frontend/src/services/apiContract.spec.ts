import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AxiosError, AxiosHeaders } from 'axios'
import { apiClient, toApiCode, toApiMessage } from '@/services/apiClient'
import { authService } from '@/services/authService'
import { loginErrorMessage, registerErrorMessage } from '@/utils/validators'
import type { ApiErrorBody } from '@/types/api'

vi.mock('@/services/apiClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/apiClient')>()
  return {
    ...actual,
    apiClient: { post: vi.fn(), patch: vi.fn(), get: vi.fn() },
  }
})

const post = vi.mocked(apiClient.post)

beforeEach(() => {
  vi.clearAllMocks()
})

function apiError(code: string, message: string): AxiosError<ApiErrorBody> {
  const err = new AxiosError<ApiErrorBody>(message)
  err.response = {
    data: { error: { code, message } },
    status: 400,
    statusText: 'Bad Request',
    headers: {},
    config: { headers: new AxiosHeaders() },
  }
  return err
}

describe('kontrak error BE', () => {
  it('toApiCode membaca error.code kontrak', () => {
    expect(toApiCode(apiError('EMAIL_TAKEN', 'Email sudah terdaftar.'))).toBe('EMAIL_TAKEN')
    expect(toApiCode(new Error('jaringan'))).toBeUndefined()
  })

  it('toApiMessage memakai pesan server', () => {
    expect(toApiMessage(apiError('X', 'Pesan server.'), 'Jatuh.')).toBe('Pesan server.')
    expect(toApiMessage(new Error('boom'), 'Jatuh.')).toBe('Jatuh.')
  })

  it('memetakan kode register BE (EMAIL_TAKEN 409)', () => {
    expect(registerErrorMessage('EMAIL_TAKEN')).toContain('sudah terdaftar')
  })

  it('memetakan kode login BE (403 EMAIL_NOT_VERIFIED)', () => {
    expect(loginErrorMessage('EMAIL_NOT_VERIFIED')).toContain('belum terverifikasi')
    expect(loginErrorMessage('INVALID_CREDENTIALS')).toContain('salah')
  })

  it('payload register FE1 mengirim phone + captchaToken', async () => {
    post.mockResolvedValue({ data: { id: 'u-2' } })
    await authService.register({
      fullName: 'Tes',
      email: 'tes@pt.id',
      password: 'Rahasia123',
      organization: 'PT Tes',
      role: 'SIGNER',
      purpose: 'testing',
      phone: '+62811',
      captchaToken: 'cap-tok',
    })
    expect(post).toHaveBeenCalledWith(
      '/auth/register',
      expect.objectContaining({ phone: '+62811', captchaToken: 'cap-tok' }),
    )
  })
})
