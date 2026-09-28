# PRD BACKEND — SignVault

**Pemilik:** BE Dev
**Folder:** `/apps/backend`, `/packages/database`, `/docs/api-docs`
**Branch:** `be/*`

---

## 1. Ruang Lingkup

Membangun API FastAPI, integrasi Supabase + Prisma, kriptografi, PDF/QR, email, notifikasi, audit, dan pengujian backend.

---

## 2. Jobdesk

- Setup FastAPI + Prisma + Supabase.
- Implementasi JWT (access + refresh), Argon2id, RBAC middleware.
- Implementasi Google OAuth (verifikasi ID Token via JWKS, auto-link by email) + onboarding profil.
- Implementasi CAPTCHA Turnstile (register/resend wajib, login opsional) + rate-limit per-path auth.
- Implementasi kriptografi: RSA-2048 PSS, ECDSA P-256, Ed25519, AES-256-GCM, SHA-256.
- Implementasi endpoint sesuai `openapi.yaml`.
- Implementasi PDF service: hash, embed QR, ekstrak QR.
- Implementasi QR service: generate payload.
- Implementasi email service: verifikasi, notifikasi.
- Implementasi notification service (in-app).
- Implementasi audit service.
- Implementasi batch signing (transaksi + optimistic locking).
- Implementasi verifikasi publik.
- Testing: unit, integration, performance 30x, tamper, wrong key, fake QR, OAuth, CAPTCHA, onboarding.
- Dokumentasi API (`openapi.yaml`).

---

## 3. Folder yang Dimiliki

- `/apps/backend/**`
- `/packages/database/**`
- `/docs/api-docs/**`

---

## 4. Endpoint Wajib

| Method | Endpoint | Role |
|---|---|---|
| POST | `/api/v1/auth/register` | Public |
| POST | `/api/v1/auth/verify-email` | Public |
| POST | `/api/v1/auth/resend-verification` | Public |
| POST | `/api/v1/auth/login` | Public |
| POST | `/api/v1/auth/refresh` | Public |
| POST | `/api/v1/auth/logout` | Auth |
| POST | `/api/v1/auth/google` | Public |
| PATCH | `/api/v1/users/me/complete-profile` | Auth |
| GET | `/api/v1/users/me` | Auth |
| POST | `/api/v1/keys/generate` | Signer |
| GET | `/api/v1/keys` | Signer |
| POST | `/api/v1/keys/{id}/revoke` | Super Admin |
| POST | `/api/v1/documents` | Org Admin |
| GET | `/api/v1/documents` | Org Admin |
| GET | `/api/v1/documents/{id}` | Auth |
| POST | `/api/v1/documents/{id}/request-sign` | Org Admin |
| GET | `/api/v1/sign-requests/pending` | Signer |
| POST | `/api/v1/sign-requests/{id}/approve` | Signer |
| POST | `/api/v1/sign-requests/batch-approve` | Signer |
| POST | `/api/v1/sign-requests/{id}/reject` | Signer |
| GET | `/api/v1/verify/{sig_id}` | Public |
| POST | `/api/v1/verify/upload` | Public |
| GET | `/api/v1/audit-logs` | Super Admin, Org Admin |
| GET | `/api/v1/notifications` | Auth |

---

## 5. Skema Database

Gunakan `packages/database/schema.prisma` sesuai PRD utama.

---

## 6. Kriptografi

- **RSA:** 2048-bit, PSS, salt 32, SHA-256.
- **ECDSA:** P-256, SHA-256.
- **Ed25519:** signature 64 byte, public key 32 byte.
- **Private key:** AES-256-GCM, KEK dari `.env`.
- **Canonicalization:** JCS/RFC 8785.
- **Yang ditandatangani:** SHA-256(PDF bytes) + `metadata_canonical`.

---

## 7. Testing Wajib

- Performance: 30x sign & verify per algoritma, PDF 1/5/10 MB.
- Ukuran signature & public key.
- Tamper: ubah 1 byte PDF → gagal.
- Wrong key: public key salah → gagal.
- Fake QR: QR palsu/dimodifikasi → gagal.
- OAuth: token palsu/kedaluwarsa/aud salah → 401, sub beda → 401, akun Google login via password → 400, auto-link EMAIL→GOOGLE sukses.
- CAPTCHA: tanpa token saat aktif → 400, bypass saat nonaktif/ENV=test.
- Onboarding: PATCH sukses → flag true, PATCH kedua → 409.
- Unit test coverage ≥ 80%.

---

## 8. Environment Variables (`.env`)

File `.env` sudah tersedia di root `apps/backend/.env`. Wajib masuk `.gitignore`.

```env
DATABASE_URL=postgresql://...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
JWT_SECRET=...
JWT_REFRESH_SECRET=...
JWT_ACCESS_EXPIRE_MINUTES=15
JWT_REFRESH_EXPIRE_DAYS=7
KEK_SECRET=...
ARGON2_MEMORY=65536
ARGON2_ITERATIONS=3
ARGON2_PARALLELISM=4
SMTP_HOST=...
SMTP_PORT=587
SMTP_USER=...
SMTP_PASS=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_ALLOWED_HD=
CAPTCHA_PROVIDER=turnstile
CAPTCHA_SECRET_KEY=
CAPTCHA_SITE_KEY=
CAPTCHA_ENABLED=false
AUTH_GOOGLE_RATE_PER_MIN=10
AUTH_REGISTER_RATE_PER_MIN=10
SENTRY_DSN=...
ENV=development
API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173
```

---

## 9. CI/CD

> **Dihapus** — CI/CD tidak dipakai sesuai perubahan PRD. Penjamin kualitas:
> verifikasi manual lokal (`ruff`, `black`, `pytest` per-file, `scripts/smoke.py`).
> Deploy staging ikut panduan `docs/deployment/staging.md`, dijalankan langsung
> sebagai proses Python (Uvicorn) di server/VM.
> **Tidak menggunakan Docker/containerization** — build & deploy bersifat native.

---

## 10. Aturan untuk AI Agent

1. Hanya edit folder milik BE.
2. Jangan ubah `openapi.yaml` tanpa PR ke `main`.
3. Jangan hardcode secret; gunakan `.env`.
4. Selalu tulis unit test.
5. Gunakan library `cryptography` Python, bukan library tidak terpercaya.
6. Ikuti format error response yang disepakati.
