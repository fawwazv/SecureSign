# PRD FRONTEND 2 — SignVault

**Pemilik:** FE2 Dev
**Fokus:** Dashboard Org Admin, Signer, Super Admin
**Branch:** `fe2/*`

> Wajib mengacu pada `design.md`.

---

## 1. Ruang Lingkup

Membangun dashboard untuk Org Admin, Signer, dan Super Admin, termasuk upload PDF, request sign, batch signing, preview PDF, dan audit log.

---

## 2. Jobdesk

- Bangun `DashboardLayout` (sidebar, header, notifikasi badge, user menu).
- Bangun Dashboard Org Admin: tabel dokumen, filter status, upload PDF, modal metadata, request sign.
- Bangun Dashboard Signer: badge "X Dokumen Menunggu", tabel pending, batch sign (checkbox), split view preview PDF, tombol tolak dengan alasan.
- Bangun Dashboard Super Admin: manajemen user, revoke key, audit log global, statistik.
- Bangun komponen domain: `DocumentCard`, `SignRequestTable`, `QRViewer`, `PDFPreview`, `StatusBadge`, `NotificationDropdown`.
- Setup `documentStore`, `useDocument`, `useSignRequest`.
- Setup router dashboard + guard role.
- Integrasi API (OpenAPI generated types).
- Testing: Vitest unit, Playwright e2e untuk dashboard.
- Dokumentasi komponen.

---

## 3. Folder yang Dimiliki

- `/apps/frontend/src/pages/admin/**`
- `/apps/frontend/src/pages/org/**`
- `/apps/frontend/src/pages/signer/**`
- `/apps/frontend/src/components/domain/**`
- `/apps/frontend/src/layouts/DashboardLayout.vue`
- `/apps/frontend/src/router/dashboard.routes.ts`
- `/apps/frontend/src/stores/documentStore.ts`
- `/apps/frontend/src/composables/useDocument.ts`
- `/apps/frontend/src/composables/useSignRequest.ts`
- `/apps/frontend/src/services/documentService.ts`

---

## 4. Acuan Desain

- Wajib baca `design.md` sebelum coding.
- Gunakan palet: putih, `#FFF1E7`, `#B5D2E6`, `#326080`, `#805232`.
- Gunakan komponen UI dari FE1 (`/components/ui`).
- Jangan modifikasi komponen UI tanpa koordinasi dengan FE1.

---

## 5. Integrasi API

- Gunakan `apiClient` dari FE1.
- Generate tipe dari OpenAPI.
- Handle role-based rendering.

---

## 6. Testing

- Unit: Vitest + Vue Test Utils.
- E2E: Playwright untuk upload, request sign, batch sign, reject.

---

## 7. Aturan untuk AI Agent

1. Hanya edit folder milik FE2.
2. Wajib mengacu `design.md`.
3. Jangan ubah halaman publik (milik FE1).
4. Jangan ubah komponen UI core (milik FE1).
5. Gunakan tipe generated dari OpenAPI.
6. Selalu responsive & accessible.
