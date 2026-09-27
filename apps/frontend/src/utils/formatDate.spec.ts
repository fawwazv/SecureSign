import { describe, expect, it } from 'vitest'
import { formatDate } from '@/utils/formatDate'

describe('formatDate', () => {
  it('memformat ISO ke id-ID dan menangani invalid', () => {
    expect(formatDate('2026-09-27T10:00:00Z')).toContain('2026')
    expect(formatDate('bukan-tanggal')).toBe('-')
  })
})
