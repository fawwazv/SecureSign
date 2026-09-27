import { describe, expect, it } from 'vitest'
import { extractTokenFromQrText, isCameraQrSupported } from '@/utils/qr'

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
})

describe('isCameraQrSupported', () => {
  it('false di lingkungan tanpa getUserMedia (cth. jsdom)', () => {
    expect(isCameraQrSupported()).toBe(false)
  })
})
