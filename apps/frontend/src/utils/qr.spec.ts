import { describe, expect, it } from 'vitest'
import { extractTokenFromQrText, extractVerifyUrl, isCameraQrSupported, parseQrPayload } from '@/utils/qr'

const JSON_QR =
  '{"v":1,"doc":"d1","sig":"sv_abc","name":"Sinta","pos":"Direktur","org":"PT Maju",' +
  '"at":"2026-09-29T10:00:00+00:00","alg":"RSA_PSS_2048","url":"https://signvault.id/verify/sv_abc"}'

describe('extractTokenFromQrText', () => {
  it('meneruskan token mentah', () => {
    expect(extractTokenFromQrText('sv_9f2c41')).toBe('sv_9f2c41')
  })

  it('mengekstrak token dari URL /verify/:token', () => {
    expect(extractTokenFromQrText('https://signvault.id/verify/sv_9f2c41')).toBe('sv_9f2c41')
  })

  it('mengekstrak token dari query ?token=', () => {
    expect(extractTokenFromQrText('https://signvault.id/verify?token=sv_abc')).toBe('sv_abc')
  })

  it('mengembalikan string kosong untuk input kosong', () => {
    expect(extractTokenFromQrText('   ')).toBe('')
  })

  it('mengekstrak sig dari JSON QR kaya', () => {
    expect(extractTokenFromQrText(JSON_QR)).toBe('sv_abc')
  })

  it('menolak JSON tanpa sig valid', () => {
    expect(extractTokenFromQrText('{"v":1,"doc":"d1"}')).toBe('{"v":1,"doc":"d1"}')
  })
})

describe('parseQrPayload / extractVerifyUrl', () => {
  it('parse field publik JSON', () => {
    const info = parseQrPayload(JSON_QR)
    expect(info?.sigId).toBe('sv_abc')
    expect(info?.name).toBe('Sinta')
    expect(info?.position).toBe('Direktur')
    expect(info?.url).toBe('https://signvault.id/verify/sv_abc')
  })

  it('bukan JSON -> null, url mentah dikembalikan', () => {
    expect(parseQrPayload('https://signvault.id/verify/sv_x')).toBeNull()
    expect(extractVerifyUrl('https://signvault.id/verify/sv_x')).toBe(
      'https://signvault.id/verify/sv_x',
    )
    expect(extractVerifyUrl(JSON_QR)).toBe('https://signvault.id/verify/sv_abc')
  })
})

describe('isCameraQrSupported', () => {
  it('false di lingkungan tanpa getUserMedia (cth. jsdom)', () => {
    expect(isCameraQrSupported()).toBe(false)
  })
})
