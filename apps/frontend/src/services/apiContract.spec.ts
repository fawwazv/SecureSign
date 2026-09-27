import { describe, expect, it } from 'vitest'
import { AxiosError, AxiosHeaders } from 'axios'
import { toApiCode, toApiMessage } from '@/services/apiClient'
import { loginErrorMessage, registerErrorMessage } from '@/utils/validators'
import type { ApiErrorBody } from '@/types/api'

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
})
