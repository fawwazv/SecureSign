import { test, expect, type Page } from '@playwright/test'

type OnboardingRole = 'SEKRETARIAT' | 'SIGNER'

function googleUser(role: OnboardingRole) {
  return {
    id: 'google-u1',
    fullName: 'Sinta',
    email: 'sinta@mail.id',
    organization: '',
    role,
    emailVerified: true,
    createdAt: '2026-09-28T00:00:00Z',
    phone: null,
    authProvider: 'GOOGLE',
    profileCompleted: false,
    avatarUrl: null,
  }
}

async function mockGoogleOnboarding(page: Page, role: OnboardingRole) {
  await page.route(/\/api\/v1\/auth\/google$/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        user: googleUser(role),
        tokens: { accessToken: 'acc-token', refreshToken: 'ref-token', expiresIn: 900 },
        profileCompleted: false,
      }),
    })
  })

  await page.route(/\/api\/v1\/users\/me\/complete-profile$/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        ...googleUser(role),
        organization: 'PT Maju',
        phone: '+628123456789',
        profileCompleted: true,
      }),
    })
  })

  if (role === 'SEKRETARIAT') {
    await page.route(/\/api\/v1\/documents(\?|$)/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ data: [], page: 1, limit: 20, total: 0 }),
      })
    })
  } else {
    await page.route(/\/api\/v1\/sign-requests\/pending(\?|$)/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ data: [], page: 1, limit: 20, total: 0 }),
      })
    })
  }
}

test.describe('Google OAuth onboarding (FE1-8)', () => {
  test('Google baru SEKRETARIAT -> onboarding -> /org', async ({ page }) => {
    await mockGoogleOnboarding(page, 'SEKRETARIAT')
    await page.goto('/auth/callback?credential=mock-google-id-token')

    await expect(page).toHaveURL(/\/onboarding$/)
    await expect(page.getByLabel('Email (dari Google)')).toHaveValue('sinta@mail.id')

    await page.getByLabel('Organisasi / Perusahaan').fill('PT Maju')
    await page.getByLabel('Nomor telepon').fill('+628123456789')
    await page.getByLabel('Keperluan penggunaan').fill('TTD kontrak')
    await page.getByRole('button', { name: 'Simpan & masuk dashboard' }).click()

    await expect(page).toHaveURL(/\/org$/)
    await expect(page.getByRole('heading', { name: 'Dokumen Saya', exact: true })).toBeVisible()
  })

  test('Google baru SIGNER -> onboarding -> /signer', async ({ page }) => {
    await mockGoogleOnboarding(page, 'SIGNER')
    await page.goto('/auth/callback?credential=mock-google-id-token')

    await expect(page).toHaveURL(/\/onboarding$/)
    await page.getByLabel('Peran').selectOption('SIGNER')
    await page.getByLabel('Organisasi / Perusahaan').fill('PT Maju')
    await page.getByLabel('Nomor telepon').fill('+628123456789')
    await page.getByLabel('Keperluan penggunaan').fill('TTD kontrak')
    await page.getByRole('button', { name: 'Simpan & masuk dashboard' }).click()

    await expect(page).toHaveURL(/\/signer$/)
    await expect(page.getByRole('heading', { name: 'Permintaan Tanda Tangan', exact: true })).toBeVisible()
  })
})
