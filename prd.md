# PRD UTAMA — SignVault

**Versi:** 1.4
**Status:** Final MVP
**Pemilik:** Product Owner
**Terakhir diperbarui:** 2026-09-29

---

## 1. Ringkasan Produk

SignVault adalah aplikasi web untuk menandatangani dokumen elektronik (PDF) secara digital, memverifikasi keaslian dokumen, dan mengelola alur persetujuan multi-pihak (*Multi-Signer Workflow*). Aplikasi ini menggantikan tanda tangan basah dengan solusi kriptografi yang aman, cepat, dan memiliki audit trail.

---

## 2. Tujuan & Ruang Lingkup MVP

- Dokumen utama: PDF.
- Tanda tangan digital: RSA-2048 PSS, ECDSA P-256, atau Ed25519.
- Workflow: Org Admin upload → Signer review → Signer tanda tangan → QR tertempel.
- Verifikasi publik tanpa login.
- Kunci privat terenkripsi AES-256-GCM.
- Registrasi email+password (1 form + CAPTCHA Turnstile) dengan verifikasi email sebelum login.
- Login Google OAuth (ID Token via GIS, verifikasi JWKS di backend) + onboarding profil bila akun baru.
- Akun email yang sama otomatis terhubung (auto-link) antara metode EMAIL dan GOOGLE.
- Landing page informatif sebelum login.
- JWT untuk autentikasi & otorisasi.
- Multi-role: Super Admin, Org Admin, Signer, Verifier.
- **Tanpa blockchain.** Bukti waktu menggunakan server-side timestamp (opsional RFC 3161 TSA).

---

## 3. Tech Stack

| Layer | Teknologi |
|---|---|
| Frontend | Vue.js 3 + TypeScript + Vite |
| UI | Shadcn Vue + Tailwind CSS |
| State | Pinia |
| Backend | Python 3.11+ + FastAPI |
| Kriptografi | Python `cryptography` |
| PDF & QR | `pypdf`, `qrcode`, `Pillow`, `pyhanko` |
| Database | Supabase (PostgreSQL) |
| ORM | Prisma (`prisma-client-py`) |
| Auth | Supabase Auth + JWT |
| Storage | Supabase Storage |
| Email | Supabase Auth / Resend / SendGrid |
| CI/CD | Verifikasi manual lokal (`ruff`, `black`, `pytest`, `smoke.py`) |
| Monitoring | Sentry, Prometheus, Grafana |

> **Catatan:** Deployment dijalankan langsung di server/VM tanpa kontainerisasi (tidak menggunakan Docker) untuk menjaga MVP tetap sederhana.

---

## 4. Peran & Hak Akses (RBAC)

| Peran | Deskripsi | Hak Akses |
|---|---|---|
| Super Admin | Pengelola platform | Manajemen user global, revoke key, audit log global. |
| Org Admin | Admin perusahaan | Upload PDF, isi metadata, minta tanda tangan, unduh dokumen. |
| Signer | Direktur/Manajer | Review, tanda tangan (single/batch), tolak dokumen, kelola key. |
| Verifier | Publik/pihak ketiga | Verifikasi via QR/upload **tanpa login**. |

---

## 5. Alur Utama

1. **Registrasi & Login** — (a) Email: form 1-langkah (kredensial + profil + CAPTCHA) → email verifikasi → akun aktif → login. (b) Google: tombol Google → onboarding profil (bila baru) → dashboard sesuai role.
2. **Multi-Signer Workflow** — Org Admin upload → request sign → notifikasi → Signer review → sign/tolak → QR tertempel → notifikasi ke Org Admin.
3. **Verifikasi Publik** — Scan QR/upload PDF → cek hash & signature → tampilkan VALID/TIDAK VALID.
4. **Landing Page** — Header, Hero, Fitur, Cara Kerja, Use Case, Keamanan, FAQ, Footer.

---

## 6. Fitur MVP Wajib

| ID | Fitur | Deskripsi |
|---|---|---|
| F-01 | Landing Page | Halaman publik sebelum login. |
| F-02 | Registrasi & Verifikasi Email | Form 1-langkah + CAPTCHA + email verifikasi. |
| F-02b | Login Google + Onboarding | OAuth Google (GIS id_token, JWKS) + lengkapi profil bila akun baru. |
| F-03 | Autentikasi & RBAC | Login email (terverifikasi) atau Google, JWT (access + refresh). |
| F-04 | Pembangkitan Kunci | RSA-2048 PSS, ECDSA P-256, Ed25519. |
| F-05 | Penyimpanan Kunci Privat | AES-256-GCM, KEK dari env/Supabase Vault. |
| F-06 | Upload PDF | Org Admin upload ke Supabase Storage. |
| F-07 | Request Signature | Org Admin minta tanda tangan ke Signer. |
| F-08 | Notifikasi | Email + In-App ke Signer. |
| F-09 | Review & Sign | Signer preview PDF, setujui/tolak. |
| F-10 | Batch Signing | Signer tanda tangani banyak dokumen sekaligus. |
| F-11 | Signing PDF | SHA-256, sign hash + metadata, sisipkan QR. |
| F-12 | QR-Code | Metadata, hash, signature/tautan verifikasi. |
| F-13 | Verifikasi Publik | Upload PDF/scan QR tanpa login. |
| F-14 | Penolakan Dokumen | Tolak jika hash/signature/kunci/QR tidak valid. |
| F-15 | Audit Log | Catat aktivitas sign/verify. |
| F-16 | Dashboard | Berbeda per role. |
| F-17 | Key Revocation | Super Admin dapat revoke key. |

---

## 7. Non-Functional Requirements

| Aspek | Ketentuan |
|---|---|
| Security | TLS 1.3, AES-256-GCM, Argon2id, JWT, RBAC, rate limit, CORS ketat. |
| Performance | Sign < 3 detik, verify < 2 detik untuk PDF 1–5 MB. |
| Availability | 99.5% untuk MVP. |
| Audit | Log immutable. |
| Compliance | UU ITE, PDP, OWASP Top 10. |
| Usability | Responsive web, QR dapat dipindai. |
| Backup | Supabase automatic backup harian. |
| Monitoring | Sentry, Prometheus, Grafana. |

---

## 8. Kriptografi & Keamanan

- **Hash:** SHA-256 atas byte PDF.
- **Algoritma:** RSA-2048 PSS (salt 32, SHA-256), ECDSA P-256 (SHA-256), Ed25519.
- **PAdES (PDF advance):** RSA/ECDSA bersertifikat self-signed ditandatangani via
  pyHanko — digest SHA-256 atas ByteRange, CMS RSASSA-PSS, appearance visual
  (nama/waktu/ID) + QR pada posisi Sekretaris; Ed25519 tetap jalur detached legacy.
- **Sertifikat:** self-signed per key (demo akademik, **bukan** PSrE tersertifikasi).
- **Private key:** AES-256-GCM, KEK dari environment variable / Supabase Vault.
- **Canonicalization:** JCS/RFC 8785.
- **JWT:** Access 15 menit, Refresh 7 hari, secret di `.env`.
- **Password:** Argon2id (64MB, 3 iterasi, 4 paralel).
- **Email token:** 32-byte random, single-use, expired 24 jam.

---

## 9. Data Model Ringkas

- Entity: `User`, `KeyPair`, `Document`, `SignRequest`, `Signature`, `AuditLog`.
- Enum Role: `SUPER_ADMIN`, `ORG_ADMIN`, `SIGNER`, `VERIFIER`.
- Detail lengkap: `packages/database/schema.prisma`.

---

## 10. API Contract

- Sumber kebenaran: `docs/api-docs/openapi.yaml`.
- FE wajib generate tipe dari OpenAPI (`openapi-typescript`).
- Perubahan API harus melalui PR ke `main` dan disetujui BE + FE lead.

---

## 11. Struktur Proyek (Monorepo)

```text
/signvault
├── /apps
│   ├── /frontend                         # Vue.js + TS + Tailwind + Shadcn
│   │   ├── /public                       # Static assets (favicon, dll)
│   │   ├── /src
│   │   │   ├── /assets
│   │   │   │   ├── /images
│   │   │   │   └── /styles
│   │   │   ├── /components
│   │   │   │   ├── /ui                   # FE1: Shadcn Vue
│   │   │   │   ├── /layout               # FE1/FE2: Header, Sidebar, Footer
│   │   │   │   └── /domain               # FE2: DocumentCard, SignRequestTable, QRViewer
│   │   │   ├── /composables
│   │   │   │   ├── useAuth.ts            # FE1
│   │   │   │   ├── useJWT.ts             # FE1
│   │   │   │   ├── useDocument.ts        # FE2
│   │   │   │   └── useSignRequest.ts     # FE2
│   │   │   ├── /layouts
│   │   │   │   ├── LandingLayout.vue     # FE1
│   │   │   │   └── DashboardLayout.vue   # FE2
│   │   │   ├── /pages
│   │   │   │   ├── /public               # FE1: Landing, Login, Register, VerifyEmail, Verify
│   │   │   │   ├── /admin                # FE2: Dashboard, Users, AuditLog
│   │   │   │   ├── /org                  # FE2: Dashboard, Upload, DocumentDetail
│   │   │   │   └── /signer               # FE2: Dashboard, SignRequestDetail, BatchSign
│   │   │   ├── /router
│   │   │   │   ├── index.ts              # FE1
│   │   │   │   ├── public.routes.ts      # FE1
│   │   │   │   ├── dashboard.routes.ts   # FE2
│   │   │   │   └── guards.ts             # FE1
│   │   │   ├── /services
│   │   │   │   ├── apiClient.ts          # FE1
│   │   │   │   ├── authService.ts        # FE1
│   │   │   │   └── documentService.ts    # FE2
│   │   │   ├── /stores
│   │   │   │   ├── authStore.ts          # FE1
│   │   │   │   ├── notificationStore.ts  # FE1
│   │   │   │   └── documentStore.ts      # FE2
│   │   │   ├── /types                    # Generated dari OpenAPI
│   │   │   ├── /utils                    # FE1: formatDate, validators
│   │   │   ├── App.vue
│   │   │   └── main.ts
│   │   ├── .env                          # FE env (wajib gitignored)
│   │   ├── index.html
│   │   ├── package.json
│   │   ├── tailwind.config.js
│   │   ├── tsconfig.json
│   │   └── vite.config.ts
│   │
│   └── /backend                          # Python FastAPI
│       ├── /app
│       │   ├── /api
│       │   │   ├── /v1
│       │   │   │   ├── auth.py
│       │   │   │   ├── users.py
│       │   │   │   ├── keys.py
│       │   │   │   ├── documents.py
│       │   │   │   ├── sign_requests.py
│       │   │   │   ├── verify.py
│       │   │   │   ├── audit_logs.py
│       │   │   │   └── notifications.py
│       │   │   └── deps.py               # get_current_user, require_role
│       │   ├── /core
│       │   │   ├── config.py             # Load dari .env
│       │   │   ├── security.py           # JWT, Argon2id, AES-GCM
│       │   │   ├── rbac.py
│       │   │   └── exceptions.py
│       │   ├── /crypto
│       │   │   ├── rsa.py
│       │   │   ├── ecdsa.py
│       │   │   ├── ed25519.py
│       │   │   ├── hashing.py
│       │   │   └── key_manager.py
│       │   ├── /models
│       │   │   └── prisma_client.py
│       │   ├── /schemas                  # Pydantic
│       │   │   ├── auth.py
│       │   │   ├── user.py
│       │   │   ├── document.py
│       │   │   ├── sign_request.py
│       │   │   └── signature.py
│       │   ├── /services
│       │   │   ├── pdf_service.py
│       │   │   ├── qr_service.py
│       │   │   ├── email_service.py
│       │   │   ├── notification_service.py
│       │   │   └── audit_service.py
│       │   ├── /tests
│       │   │   ├── test_auth.py
│       │   │   ├── test_crypto.py
│       │   │   ├── test_signing.py
│       │   │   ├── test_verify.py
│       │   │   └── test_tamper.py
│       │   └── main.py
│       ├── .env                          # BE env (wajib gitignored)
│       ├── pyproject.toml
│       └── requirements.txt
│
├── /packages
│   └── /database                         # Prisma Schema
│       ├── schema.prisma
│       ├── /migrations
│       └── seed.ts
│
├── /docs
│   ├── /product-backlog
│   │   └── product-backlog.md
│   ├── /sprint-backlog
│   │   ├── sprint-0.md
│   │   ├── sprint-1.md
│   │   ├── sprint-2.md
│   │   ├── sprint-3.md
│   │   ├── sprint-4.md
│   │   └── sprint-5.md
│   ├── /definition-of-done
│   │   └── dod.md
│   ├── /architecture-decision-records
│   │   ├── ADR-001-python-fastapi.md
│   │   ├── ADR-002-supabase-prisma.md
│   │   └── ADR-003-multi-signer-workflow.md
│   └── /api-docs
│       └── openapi.yaml
│
├── /tests
│   ├── /e2e                              # Playwright
│   │   ├── auth.spec.ts
│   │   ├── signing.spec.ts
│   │   └── verify.spec.ts
│   └── /performance                      # Locust / k6
│       ├── sign_test.py
│       └── verify_test.py
│
├── .env                                  # Root env (opsional, wajib gitignored)
├── .gitignore
├── CONTRIBUTING.md
├── SECURITY.md
├── README.md
└── LICENSE
```

> Struktur ini dijalankan langsung sebagai proses native (Vite dev server & Uvicorn) — **tidak ada Dockerfile atau docker-compose** dalam proyek ini.

---

## 12. Struktur Tim & Kepemilikan Folder

| Peran | Folder yang Dimiliki |
|---|---|
| Backend (BE) | `/apps/backend/**`, `/packages/database/**`, `/docs/api-docs/**` |
| Frontend 1 (FE1) | `/apps/frontend/src/components/ui/**`, `/pages/public/**`, `/layouts/LandingLayout.vue`, `/assets/styles/**`, `/router/index.ts`, `/router/public.routes.ts`, `/router/guards.ts`, `/stores/authStore.ts`, `/stores/notificationStore.ts`, `/composables/useAuth.ts`, `/composables/useJWT.ts`, `/services/apiClient.ts`, `/services/authService.ts`, `/utils/**`, `/types/**`, `/public/**`, `tailwind.config.js`, `vite.config.ts`, `index.html`, `apps/frontend/.env` |
| Frontend 2 (FE2) | `/apps/frontend/src/pages/admin/**`, `/pages/org/**`, `/pages/signer/**`, `/components/domain/**`, `/layouts/DashboardLayout.vue`, `/router/dashboard.routes.ts`, `/stores/documentStore.ts`, `/composables/useDocument.ts`, `/composables/useSignRequest.ts`, `/services/documentService.ts` |

**Aturan:** Dilarang mengubah file di luar folder miliknya tanpa PR dan persetujuan pemilik folder.

---

## 13. Strategi Branch & Commit

- Branch utama: `main` (protected).
- Branch pengembangan: `develop` (protected).
- Branch fitur: `be/feature-xxx`, `fe1/feature-xxx`, `fe2/feature-xxx`.
- Commit message: `feat(scope): deskripsi` / `fix(scope): deskripsi`.
- PR wajib: minimal 1 reviewer, lolos CI, tidak ada konflik.
- Dilarang push langsung ke `main` atau `develop`.

---

## 14. Definition of Done (DoD)

- ✅ Fitur berjalan di staging.
- ✅ Lolos unit & integration test (coverage ≥ 80%).
- ✅ Tidak ada hardcoded secret.
- ✅ Dokumentasi API diperbarui.
- ✅ Kode di-review minimal 1 anggota lain.
- ✅ Tidak ada bug critical/high.
- ✅ Demo ke Product Owner disetujui.

---

## 15. Sprint Plan

| Sprint | Durasi | Fokus |
|---|---|---|
| Sprint 0 | 1 Minggu | Setup monorepo, Supabase, Prisma, Vue + Shadcn, FastAPI, JWT, Landing Page statis, CI/CD. |
| Sprint 1 | 2 Minggu | Autentikasi (email + Google OAuth), verifikasi email, CAPTCHA, onboarding profil, RBAC, generate key pair, enkripsi private key. |
| Sprint 2 | 2 Minggu | Upload PDF, metadata, SignRequest, notifikasi, dashboard Org Admin. |
| Sprint 3 | 2 Minggu | Dashboard Signer, preview PDF, single & batch signing, QR generation. |
| Sprint 4 | 1 Minggu | Verifikasi publik, uji tamper, audit log, pengujian performa 30x. |
| Sprint 5 | 1 Minggu | Polish, dokumentasi, deployment staging, demo. |

---

## 16. Risiko & Mitigasi

| Risiko | Mitigasi |
|---|---|
| QR terlalu besar | Gunakan tautan verifikasi. |
| Private key bocor | KMS/Vault, AES-256-GCM, audit, revoke. |
| Signer enggan login | Batch signing, magic link, in-app notification. |
| Legalitas | Integrasi PSrE jika produksi. |
| PDF berubah | ByteRange PAdES + detached signature + hash verification. |
| Sertifikat self-signed tak dipercaya Adobe | Ekspektasi demo; label jelas bukan PSrE; produksi wajib sertifikat tersertifikasi. |
| Fake QR | Signature metadata + server-side validation. |
| Performa RSA besar | Default ECDSA/Ed25519. |
| JWT bocor | Access token pendek, refresh rotation. |
| Race condition batch sign | Database transaction + optimistic locking. |
| `.env` bocor ke repo | `.gitignore` wajib, pre-commit hook (gitleaks). |

---

## 17. Catatan Legal

MVP ini adalah prototipe teknis. Tanda tangan PAdES memakai sertifikat self-signed
(ditampilkan Adobe sebagai tidak tepercaya — benar dan ekspektasi). Untuk kekuatan
hukum penuh di Indonesia, perlu integrasi dengan PSrE/TTE tersertifikasi, e-KYC,
dan e-Meterai.

---

## 18. Aturan untuk AI Agent

1. Baca `prd.md`, PRD spesifik peran, dan `design.md` (khusus FE) sebelum menulis kode.
2. Hanya boleh mengubah file di folder yang dimiliki sesuai PRD peran.
3. Dilarang mengubah API contract tanpa PR ke `main`.
4. Dilarang menulis secret di kode; gunakan `.env`.
5. Selalu jalankan test sebelum commit.
6. Untuk FE: wajib menggunakan design token dari `design.md`.
7. Jika ragu, tanyakan ke Product Owner via issue, jangan berasumsi.

---

## 19. Konvensi & Ketentuan Tambahan

- API versioning: `/api/v1`.
- Format error: `{ "error": { "code": "...", "message": "..." } }`.
- Pagination: `?page=1&limit=20`.
- Batas ukuran file: 25 MB.
- Rate limiting: 60 req/menit per IP.
- CORS: hanya domain FE.
- Audit log: tidak bisa dihapus/diubah.
- Key rotation: revoke + generate baru.
- Backup & DR: Supabase PITR.
- Monitoring & alerting: Sentry + Grafana.
- Deployment: proses native (Uvicorn untuk backend, static build untuk frontend) — **tanpa Docker/containerization**.
- Lisensi: MIT.
- Wajib membaca: `CONTRIBUTING.md` dan `SECURITY.md`.
