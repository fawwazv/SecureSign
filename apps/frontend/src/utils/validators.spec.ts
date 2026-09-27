import { describe, expect, it } from 'vitest'
import { isEmail, isStrongPassword } from '@/utils/validators'

describe('validators', () => {
  it('menerima email valid dan menolak yang invalid', () => {
    expect(isEmail('nama@perusahaan.id')).toBe(true)
    expect(isEmail('bukan-email')).toBe(false)
    expect(isEmail('a@b')).toBe(false)
  })

  it('menerima password kuat (huruf + angka, min 8)', () => {
    expect(isStrongPassword('Rahasia123')).toBe(true)
    expect(isStrongPassword('pendek1')).toBe(false)
    expect(isStrongPassword('tanpaangka')).toBe(false)
  })
})
