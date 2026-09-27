import { test, expect } from '@playwright/test'

test.describe('alur publik SignVault (FE1)', () => {
  test('landing memuat hero + CTA', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByRole('heading', { name: /tanda tangan pdf/i })).toBeVisible()
    await expect(page.getByRole('link', { name: /mulai gratis/i })).toBeVisible()
    await expect(page.getByRole('link', { name: /verifikasi dokumen/i })).toBeVisible()
  })

  test('register menampilkan 6 field', async ({ page }) => {
    await page.goto('/register')
    for (const label of ['Nama lengkap', 'Email', 'Kata sandi', 'Organisasi', 'Peran', 'Keperluan']) {
      await expect(page.getByLabel(new RegExp(label, 'i')).first()).toBeVisible()
    }
  })

  test('halaman verify publik bisa diakses tanpa login', async ({ page }) => {
    await page.goto('/verify')
    await expect(page.getByRole('heading', { name: /verifikasi dokumen/i })).toBeVisible()
    await expect(page.getByRole('tab', { name: /upload pdf/i })).toBeVisible()
  })
})
