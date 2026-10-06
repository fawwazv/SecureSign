import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { assertPdfFile, runBenchmark } from './documentService'
import { useDocumentStore } from '@/stores/documentStore'

function pdf(name = 'dok.pdf', size = 1024): File {
  const blob = new Blob([new Uint8Array(size)], { type: 'application/pdf' })
  return new File([blob], name, { type: 'application/pdf' })
}

describe('documentService.assertPdfFile', () => {
  it('menerima PDF valid ≤25MB', () => {
    expect(() => assertPdfFile(pdf())).not.toThrow()
  })

  it('menolak non-PDF', () => {
    const f = new File(['x'], 'a.txt', { type: 'text/plain' })
    expect(() => assertPdfFile(f)).toThrow('PDF')
  })

  it('menolak PDF >25MB', () => {
    const big = pdf('big.pdf', 25 * 1024 * 1024 + 1)
    expect(() => assertPdfFile(big)).toThrow('25 MB')
  })
})

describe('runBenchmark validasi sisi klien', () => {
  it('menolak iterasi < 30 tanpa request jaringan', async () => {
    await expect(runBenchmark(pdf(), 29)).rejects.toThrow('30')
  })

  it('menolak file non-PDF', async () => {
    const f = new File(['x'], 'a.txt', { type: 'text/plain' })
    await expect(runBenchmark(f, 30)).rejects.toThrow('PDF')
  })
})

describe('documentStore seleksi batch', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('toggleSelect menambah & menghapus id', () => {
    const s = useDocumentStore()
    s.toggleSelect('a')
    expect(s.selectedIds).toEqual(['a'])
    expect(s.hasSelection).toBe(true)
    s.toggleSelect('a')
    expect(s.selectedIds).toEqual([])
    s.toggleSelect('a')
    s.clearSelection()
    expect(s.selectedIds).toEqual([])
  })

  it('setStatusFilter mereset halaman', () => {
    const s = useDocumentStore()
    s.documentsPage = 3
    s.setStatusFilter('PENDING')
    expect(s.statusFilter).toBe('PENDING')
    expect(s.documentsPage).toBe(1)
  })
})
