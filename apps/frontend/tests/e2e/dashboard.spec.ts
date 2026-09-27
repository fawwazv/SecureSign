import { expect, test } from '@playwright/test'

/**
 * E2E dashboard FE2: guard role-based.
 * Tanpa backend, yang diverifikasi adalah rute terproteksi
 * mengarah ke /login bila belum login (requireAuth FE1).
 */
test.describe('guard dashboard SignVault (FE2)', () => {
  for (const path of ['/org', '/org/upload', '/signer', '/signer/batch', '/admin', '/admin/audit']) {
    test(`tamu ke ${path} dialihkan ke /login`, async ({ page }) => {
      await page.goto(path)
      await expect(page).toHaveURL(/\/login/)
    })
  }
})
