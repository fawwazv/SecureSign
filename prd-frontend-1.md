# PRD FRONTEND 1 — SignVault

**Pemilik:** FE1 Dev
**Fokus:** Public Pages & Design System
**Branch:** `fe1/*`

> Wajib mengacu pada `design.md`.

---

## 1. Ruang Lingkup

Membangun design system, landing page, halaman autentikasi, verifikasi email, verifikasi publik, dan layout publik.

---

## 2. Jobdesk

- Setup Tailwind + Shadcn Vue + design token dari `design.md`.
- Bangun komponen UI dasar: Button, Input, Card, Badge, Alert, Modal, Table, Tabs.
- Bangun Landing Page (Header, Hero, Fitur, Cara Kerja, Use Case, Keamanan, FAQ, Footer).
- Bangun halaman Register (6 field sesuai lampiran).
- Bangun halaman Login + Lupa Password.
- Bangun halaman Verifikasi Email (sukses/gagal, kirim ulang).
- Bangun halaman Verifikasi Publik (upload/scan QR, hasil VALID/TIDAK VALID, audit trail singkat).
- Setup router publik + guard (redirect jika belum login).
- Setup `authStore` & `notificationStore` (Pinia).
- Setup `useAuth`, `useJWT`, `apiClient` dengan interceptor JWT.
- Generate tipe dari `openapi.yaml` ke `/types`.
- Testing: Vitest unit, Playwright e2e untuk flow publik.
- Dokumentasi komponen di Storybook (opsional).

---

## 3. Folder yang Dimiliki

- `/apps/frontend/src/components/ui/**`
- `/apps/frontend/src/pages/public/**`
- `/apps/frontend/src/layouts/LandingLayout.vue`
- `/apps/frontend/src/assets/styles/**`
- `/apps/frontend/src/router/index.ts`
- `/apps/frontend/src/router/public.routes.ts`
- `/apps/frontend/src/router/guards.ts`
- `/apps/frontend/src/stores/authStore.ts`
- `/apps/frontend/src/stores/notificationStore.ts`
- `/apps/frontend/src/composables/useAuth.ts`
- `/apps/frontend/src/composables/useJWT.ts`
- `/apps/frontend/src/services/apiClient.ts`
- `/apps/frontend/src/services/authService.ts`
- `/apps/frontend/src/utils/**`
- `/apps/frontend/src/types/**` (generated)
- `/apps/frontend/public/**`
- `/apps/frontend/tailwind.config.js`
- `/apps/frontend/vite.config.ts`
- `/apps/frontend/index.html`
- `/apps/frontend/.env`

---

## 4. Acuan Desain

- Wajib baca `design.md` sebelum coding.
- Gunakan palet: putih, `#FFF1E7`, `#B5D2E6`, `#326080`, `#805232`.
- Gunakan design token Tailwind yang sudah didefinisikan.
- Jangan buat warna baru di luar palet.
- Konsisten spacing, radius, shadow, typography.

---

## 5. Environment Variables (`.env`)

File `.env` sudah tersedia di `apps/frontend/.env`. Wajib masuk `.gitignore`.

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=...
VITE_APP_NAME=SignVault
```

---

## 6. Integrasi API

- Gunakan `apiClient` dengan base URL dari `.env`.
- Generate tipe dari OpenAPI.
- Handle error 401 → redirect login, 403 → halaman forbidden.

---

## 7. Testing

- Unit: Vitest + Vue Test Utils.
- E2E: Playwright untuk register, login, verifikasi publik.

---

## 8. Aturan untuk AI Agent

1. Hanya edit folder milik FE1.
2. Wajib mengacu `design.md`.
3. Jangan ubah halaman dashboard (milik FE2).
4. Jangan ubah `openapi.yaml`.
5. Gunakan komponen Shadcn Vue yang sudah ada.
6. Selalu responsive & accessible.
