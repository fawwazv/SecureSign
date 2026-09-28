# UPDATE OTORISASI — Google OAuth + Onboarding + CAPTCHA

> Dokumen eksekusi untuk AI agent. Bahasa: Indonesia.
> Status: RENCANA — belum dieksekusi. Jalankan sekuens §9 dari atas ke bawah.
> Keputusan terkunci: **Opsi A (BE verifikasi ID Token Google, tetap JWT internal) + Cloudflare Turnstile + form email 1-langkah**.

## 1. Tujuan

1. Skenario 1 (Google): user daftar/masuk via Google Cloud Console OAuth → redirect ke pengisian profil (email readonly, no telepon, role, organisasi, purpose) → redirect ke dashboard sesuai role.
2. Skenario 2 (Email+Password): register 1 form sekaligus (kredensial + profil + CAPTCHA) → verifikasi email → login.
3. Semua response error tetap `{error:{code,message}}` (`apps/backend/app/core/exceptions.py:22`).

## 2. Prasyarat Manual (manusia, sekali)

Google Cloud Console:
1. `APIs & Services > Credentials > Create OAuth Client ID > Web application`.
2. `Authorized JavaScript origins`: `http://localhost:5173`, URL staging/prod FE.
3. `Authorized redirect URIs`: `http://localhost:5173/auth/callback` (+ staging/prod). Jika BE pakai code-exchange, tambah `http://localhost:8000/api/v1/auth/google/callback`.
4. Catat `GOOGLE_CLIENT_ID` (public) dan `GOOGLE_CLIENT_SECRET` (rahasia, hanya BE).
5. Cloudflare Dashboard > Turnstile > Add site > salin `Site Key` (public) dan `Secret Key` (rahasia BE).

## 3. Perubahan Data Model (BE wajib pertama)

File: `packages/database/schema.prisma` (sekarang `model User` di baris 41-64, `passwordHash String` NOT NULL).

### 3.1 Prisma diff yang harus diterapkan

```prisma
enum AuthProvider {
  EMAIL
  GOOGLE
}

model User {
  id                String    @id @default(cuid())
  email             String    @unique
  passwordHash      String?   @map("password_hash") // NULL untuk user Google-only
  fullName          String    @map("full_name")
  organization      String?
  phone             String?
  role              Role      @default(SIGNER)
  authProvider      AuthProvider @default(EMAIL) @map("auth_provider")
  googleSub         String?   @unique @map("google_sub")
  avatarUrl         String?   @map("avatar_url")
  profileCompleted  Boolean   @default(false) @map("profile_completed")
  emailVerified     Boolean   @default(false) @map("email_verified")
  verificationToken String?   @map("verification_token")
  verificationExpiry DateTime? @map("verification_expiry")
  // ... relasi & createdAt/updatedAt tetap
}
```

Aturan migrasi:
1. `passwordHash` jadi nullable. User lama biarkan terisi.
2. Backfill satu kali: `UPDATE users SET auth_provider='EMAIL', profile_completed=true WHERE email_verified=true;` user belum verifikasi biarkan `false`.
3. `googleSub` UNIQUE nullable (di Postgres, banyak NULL boleh).
4. Cara migrasi: `cd packages/database && prisma migrate dev --name add_oauth_profile` lalu `prisma generate`. Runtime tetap pakai `DATABASE_URL` pooler, DDL pakai `DIRECT_URL` (lihat header `schema.prisma:1-3`).

## 4. Backend — Env & Config

File: `apps/backend/.env.example`, `apps/backend/.env` (jangan commit), `apps/backend/app/core/config.py:43-75`.

Tambah ke `.env.example` + `Settings`:

```env
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_ALLOWED_HD=
CAPTCHA_PROVIDER=turnstile
CAPTCHA_SECRET_KEY=
CAPTCHA_SITE_KEY=
CAPTCHA_ENABLED=true
AUTH_GOOGLE_RATE_PER_MIN=10
AUTH_REGISTER_RATE_PER_MIN=10
```

Implementasi `config.py`:
- Tambah field `google_client_id: str = ""`, `google_client_secret`, `google_allowed_hd`, `captcha_provider`, `captcha_secret_key`, `captcha_site_key`, `captcha_enabled: bool`, rate khusus auth.
- Validasi saat startup: jika `ENV=production` dan `CAPTCHA_ENABLED=true` maka `CAPTCHA_SECRET_KEY` wajib; jika Google dipakai maka `GOOGLE_CLIENT_ID` wajib. Gunakan helper `_req`/`_int` yang sudah ada, tambah `_bool`.

## 5. Backend — Service Baru

### 5.1 `apps/backend/app/services/google_auth.py` (baru)

Tugas: `verify_google_id_token(id_token: str) -> dict{ sub, email, email_verified, name, picture, hd }`.

Spesifikasi:
- Ambil JWKS `https://www.googleapis.com/oauth2/v3/certs` via `httpx` (sudah ada di `requirements.txt:15`), cache 1 jam di memori.
- Verifikasi RS256 dengan `python-jose` (sudah ada `requirements.txt:8`), cek: `iss in (accounts.google.com, https://accounts.google.com)`, `aud == settings.google_client_id`, `exp` valid.
- Jika `settings.google_allowed_hd` diisi, tolak `hd` yang tidak cocok → `AppError("GOOGLE_HD_NOT_ALLOWED", ..., 403)`.
- Wajib `email_verified == true` dari Google, jika tidak → `AppError("GOOGLE_EMAIL_NOT_VERIFIED", ..., 400)`.
- Timeout HTTP 5 detik, error jaringan → `AppError("GOOGLE_VERIFY_FAILED", "Verifikasi Google gagal.", 502)`.
- Tulis unit test dengan JWKS mock, jangan panggil Google asli di test.

### 5.2 `apps/backend/app/services/captcha_service.py` (baru)

Tugas: `async def verify_captcha(token: str | None, ip: str | None) -> None` (raise jika gagal).

Spesifikasi:
- Jika `settings.captcha_enabled` false ATAU `ENV=test` → return (bypass, tapi log).
- Provider `turnstile`: `POST https://challenges.cloudflare.com/turnstile/v0/siteverify` body `{secret, response: token, remoteip: ip}`, timeout 5s via `httpx.AsyncClient`.
- Sukses jika `json.success is true`. Gagal → `AppError("CAPTCHA_FAILED", "Verifikasi CAPTCHA gagal.", 400)`. Jangan bedakan token kosong vs salah di pesan ke klien.
- Dipakai di `POST /auth/register` (wajib), `POST /auth/resend-verification` (wajib), `POST /auth/login` (opsional: hanya jika butuh; minimal terapkan setelah 3x gagal — untuk MVP boleh wajib dengan flag env agar sederhana).

Tambah `httpx` sudah tersedia, tidak perlu dep baru.

## 6. Backend — Schema Pydantic

File: `apps/backend/app/schemas/auth.py:1-63`, `apps/backend/app/schemas/user.py:1-35`.

### 6.1 `schemas/auth.py`

```python
class RegisterRequest(BaseModel):  # alias camelCase tetap
    full_name: str = Field(alias="fullName", min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    organization: str = Field(min_length=2, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    role: Literal["ORG_ADMIN","SIGNER"]
    purpose: str = Field(min_length=3, max_length=500)
    captcha_token: str | None = Field(alias="captchaToken", default=None)

class GoogleLoginRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id_token: str = Field(alias="idToken", min_length=1)

class CompleteProfileRequest(BaseModel):
    full_name: str = Field(alias="fullName", min_length=3, max_length=100)
    organization: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=7, max_length=20)
    role: Literal["ORG_ADMIN","SIGNER"]
    purpose: str = Field(min_length=3, max_length=500)

class GoogleLoginResponse(BaseModel):  # = LoginResponse + flag
    user: UserResponse
    tokens: AuthTokensResponse
    profile_completed: bool = Field(alias="profileCompleted")
```

Validasi phone: regex `^[+0-9][0-9\s\-()]{6,19}$`, normalisasi strip spasi.

### 6.2 `schemas/user.py`

Tambah ke `UserResponse`: `phone: str | None (alias phone)`, `authProvider (alias authProvider)`, `profileCompleted (alias profileCompleted)`, `avatarUrl | None`. Update `to_user_response()` membaca atribut camelCase Prisma (`user.phone`, `user.authProvider`, dst) dengan fallback `""`/`None` agar user lama tidak crash. `organization` tetap fallback `""`.

## 7. Backend — Endpoint

File utama: `apps/backend/app/api/v1/auth.py:1-192`, `apps/backend/app/api/v1/users.py:1-26`. Format error via `AppError` (`core/exceptions.py:13`).

### 7.1 `POST /api/v1/auth/register` (ubah, bukan tambah)

Urutan wajib:
1. `await verify_captcha(payload.captcha_token, _client_ip(request))` — paling dulu, sebelum cek DB (hemat DB dari bot).
2. Cek `existing = find_unique(email)` → `409 EMAIL_TAKEN` (tetap).
3. `create` dengan `authProvider=EMAIL, profileCompleted=true, emailVerified=false, phone=payload.phone` + token verifikasi 24 jam (kode lama `auth.py:73-96` tetap, tambah field baru).
4. `send_verification_email` + `log_action("REGISTER", details={role, hasCaptcha:true})`.
5. Response `201 UserResponse` (skema baru §6.2).

Test lama `apps/backend/app/tests/test_auth.py:53-67` harus diupdate: kirim `phone` + `captchaToken` (atau mock bypass). Jangan hapus test lama, update helper `_register`.

### 7.2 `POST /api/v1/auth/google` (baru, public)

Request: `{ "idToken": "<google id_token>" }`.
Response `200`: `{ user, tokens, profileCompleted }`.

Pseudocode wajib:

```python
claims = verify_google_id_token(payload.id_token)  # raise AppError jika invalid
email = claims["email"].lower().strip()
user = await db.user.find_unique(where={"email": email})
if user is None:
    user = await db.user.create(data={
      "email": email, "passwordHash": None,
      "fullName": claims.get("name") or email.split("@")[0],
      "avatarUrl": claims.get("picture"),
      "authProvider": "GOOGLE", "googleSub": claims["sub"],
      "emailVerified": True, "profileCompleted": False,
      "role": "SIGNER",
    })
    await log_action(db, "GOOGLE_REGISTER", actor_id=user.id, ...)
else:
    if user.googleSub and user.googleSub != claims["sub"]:
        raise AppError("INVALID_GOOGLE_SUBJECT", ..., 401)
    if user.authProvider == "EMAIL" and not user.googleSub:
        # auto-link karena email sudah diverifikasi Google
        user = await db.user.update(where={"id": user.id},
          data={"googleSub": claims["sub"], "avatarUrl": claims.get("picture"),
                "emailVerified": True})
        await log_action(db, "GOOGLE_LINK", ...)
tokens = await _issue_token_pair(db, user)  # fungsi lama auth.py:51
await log_action(db, "GOOGLE_LOGIN", ...)
return {"user": to_user_response(user), "tokens": tokens,
        "profileCompleted": user.profileCompleted}
```

Rate-limit: endpoint ini max 10/menit/IP (lihat §8).

### 7.3 `PATCH /api/v1/users/me/complete-profile` (baru, auth)

Auth: `Depends(get_current_user)` (`app/api/deps.py:14`). Request `CompleteProfileRequest` §6.1.

Logic:
1. Load user; jika `profileCompleted` true → `409 PROFILE_ALREADY_COMPLETED` (idempoten aman).
2. Update `fullName, organization, phone, role, profileCompleted=true`. `purpose` tidak ada kolom user → simpan ke audit `details.purpose` (konsisten dengan `auth.py:93`).
3. `log_action("PROFILE_COMPLETE", details={role, purpose})`.
4. Return `UserResponse` baru. FE lalu panggil `roleHome()` untuk redirect (lihat §11).

### 7.4 `POST /api/v1/auth/login` (ubah kecil)

- Setelah load user: jika `user.authProvider=="GOOGLE" and not user.passwordHash` → `400 GOOGLE_ACCOUNT_USE_SSO` ("Akun ini memakai Login Google.").
- Tambah captcha check (sesuai §5.2) + audit `LOGIN` tetap (`auth.py:144-156`).
- Response tambah `profileCompleted`? Minimal FE panggil `GET /users/me` setelah login untuk baca flag. Rekomendasi: kembalikan `LoginResponse` lama agar kompatibel, FE cek `user.profileCompleted`.

### 7.5 `GET /api/v1/users/me` (ubah kecil)

Return skema baru §6.2, tidak ada logic baru (`users.py:18-26`).

## 8. Backend — Rate Limit, Audit, Error Code

- `apps/backend/app/core/rate_limit.py:16`: tambah whitelist `/health` tetap; tambah peta limit per-path: `/auth/register`, `/auth/google`, `/auth/login`, `/auth/resend-verification` → 10/menit/IP; sisanya ikut `settings.rate_limit_per_minute`. Sediakan `reset_rate_limiter()` tetap untuk test.
- Audit `action` baru: `GOOGLE_REGISTER, GOOGLE_LOGIN, GOOGLE_LINK, PROFILE_COMPLETE, CAPTCHA_FAILED`. Pakai `log_action` yang sudah ada (`auth.py:91`).
- Kode error baru (semua via `error_body`): `CAPTCHA_FAILED(400), GOOGLE_VERIFY_FAILED(502), GOOGLE_EMAIL_NOT_VERIFIED(400), INVALID_GOOGLE_SUBJECT(401), GOOGLE_ACCOUNT_USE_SSO(400), PROFILE_ALREADY_COMPLETED(409), PROFILE_INCOMPLETE(403, opsional untuk guard BE di endpoint sensitif), ACCOUNT_LINK_REQUIRED(409, jika tim pilih manual-link ketimbang auto-link)`.
- CORS: pastikan `settings.frontend_url` mencakup domain callback (`app/main.py:30-36`).

## 9. Backend — OpenAPI & Test

- `docs/api-docs/openapi.yaml` (saat ini auth di baris 30-160, `RegisterRequest` 610-630, `User` 669-687): update via PR ke `main` (aturan `prd.md:10`):
  - `RegisterRequest += phone?, captchaToken?`; `User += phone, authProvider, profileCompleted, avatarUrl`; tambah `GoogleLoginRequest, CompleteProfileRequest, GoogleLoginResponse`; tambah path `POST /auth/google`, `PATCH /users/me/complete-profile`; tambah kode error §8 ke `components/responses`.
- Test BE (`apps/backend/app/tests/test_auth.py:1-211` + file baru `test_google_auth.py`, `test_captcha.py`, `test_onboarding.py`):
  - Update helper `_register` kirim `phone` + `captchaToken="test-bypass"` + `reset_rate_limiter()` tiap test (pola lama baris 53-67).
  - `test_google_auth.py`: mock `verify_google_id_token` → register baru `profileCompleted=false`; login ulang user sama → `true` setelah complete; `googleSub` beda ditolak 401; linking EMAIL→GOOGLE sukses + `emailVerified` true.
  - `test_captcha.py`: tanpa token ditolak 400 saat `CAPTCHA_ENABLED=true`; bypass saat `ENV=test`.
  - `test_onboarding.py`: PATCH sukses → role berubah + flag true; PATCH kedua 409; `GET /me` memuat flag.
  - Coverage target ≥80% (aturan `prd-backend.md:10`).

## 10. Frontend — Env & Dependensi

File: `apps/frontend/.env.example` (sekarang 4 baris), `apps/frontend/src/services/apiClient.ts:1-8`, `package.json:17-32`.

1. Tambah env:
   ```
   VITE_GOOGLE_CLIENT_ID=
   VITE_CAPTCHA_SITE_KEY=
   VITE_API_BASE_URL=http://localhost:8000/api/v1
   ```
2. Google Identity Services: TANPA npm baru — tambah `<script src="https://accounts.google.com/gsi/client" async defer>` di `apps/frontend/index.html`. Jangan simpan client secret di FE.
3. Turnstile: tambah `<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer>` di `index.html`, bungkus di komponen agar bisa di-mock di test.
4. Setelah `openapi.yaml` berubah, regenerate: `npx openapi-typescript ../../docs/api-docs/openapi.yaml -o src/types/openapi.d.ts`, lalu sync alias di `src/types/api.ts:25-30` (`User, RegisterPayload, + GoogleLoginPayload, CompleteProfilePayload, GoogleLoginResponse`).

## 11. Frontend — Service, Store, Composable

File: `apps/frontend/src/services/authService.ts:1-60`, `stores/authStore.ts:1-105`, `composables/useAuth.ts:1-19`, `services/apiClient.ts:103-116`.

### 11.1 `authService.ts` (tambah, jangan hapus yang ada)

```ts
loginWithGoogle(idToken: string): Promise<GoogleLoginResponse> // POST /auth/google {idToken}
completeProfile(payload: CompleteProfilePayload): Promise<User> // PATCH /users/me/complete-profile
register(payload: RegisterPayload & {phone?: string; captchaToken?: string}): Promise<User>
```

`verifyService` (baris 64-80) tidak diubah.

### 11.2 `authStore.ts` (ubah)

- State tambah `profileCompleted: boolean | null` (hydrate dari `user.profileCompleted` + `localStorage sv:user`).
- Getter tambah `needsOnboarding = isAuthenticated && profileCompleted===false`.
- Action baru:
  - `loginWithGoogle(idToken)` → `hydrateFromLoginResponse(resp)` + simpan `profileCompleted=resp.profileCompleted`, return `{user, needsOnboarding}`.
  - `completeProfile(payload)` → `authService.completeProfile` → update `user` + localStorage, return user.
- `hydrateFromLoginResponse` (baris 83-92) tetap simpan token via `useJWT`, tambah simpan user baru.
- `roleHome()` (baris 40-51) tetap `/admin|/org|/signer`, tapi panggil HANYA jika `!needsOnboarding`.
- `logout` (baris 94-103) tambah hapus `google_credential` jika ada.
- Error mapping: tambah kode §8 ke `utils/validators.ts:17-42` (`CAPTCHA_FAILED→"Verifikasi CAPTCHA gagal..."`, `GOOGLE_ACCOUNT_USE_SSO→"Akun ini memakai Login Google..."`).

### 11.3 `useAuth.ts` — expose `loginWithGoogle, completeProfile, needsOnboarding`.

## 12. Frontend — Halaman & Router

File: `pages/public/RegisterPage.vue:1-135`, `pages/public/LoginPage.vue:1-102`, `router/public.routes.ts:1-57`, `router/guards.ts:1-38`, `router/dashboard.routes.ts:1-102`.

### 12.1 `RegisterPage.vue` (ubah)

- Tambah field `phone` (Input tel, validasi regex §6.1) + widget Turnstile (komponen baru `src/components/auth/TurnstileWidget.vue`, emit `token`, reset tiap submit gagal).
- `form` tambah `phone, captchaToken`; `canSubmit` wajib `captchaToken` terisi (kecuali dev tanpa key → warning, tetap boleh submit agar test lokal jalan).
- `onSubmit` (baris 118-134) kirim `phone, captchaToken` ke `register()`. Error `CAPTCHA_FAILED` → reset widget + pesan.
- Tambah tombol/divider `"atau"` + komponen `GoogleSignInButton.vue` (lihat §12.4).

### 12.2 `LoginPage.vue` (ubah)

- Tambah `GoogleSignInButton` di atas form + divider.
- `onSubmit` (baris 79-101) setelah `login()`: jika `store.needsOnboarding` → `router.replace('/onboarding')`; else lanjut redirect `?redirect` / role (kode baris 88-93 tetap). Jika `EMAIL_NOT_VERIFIED` → ke `/verify-email` (tetap). Jika `GOOGLE_ACCOUNT_USE_SSO` → tampilkan pesan + sorot tombol Google.

### 12.3 Halaman baru (FE1)

- `src/pages/public/AuthCallback.vue` (`/auth/callback`): baca `credential` (One-Tap) atau `code` dari GIS, panggil `loginWithGoogle`, lalu `if needsOnboarding → /onboarding else roleHome()`. Tangani error `INVALID_GOOGLE_SUBJECT/GOOGLE_VERIFY_FAILED` dengan Alert + link kembali `/login`. Daftarkan di `public.routes.ts` TANPA `guestOnly`.
- `src/pages/public/OnboardingPage.vue` (`/onboarding`, `requireAuth` + bukan `guestOnly`): form `fullName (prefill dari Google name), organization, phone, role (select ORG_ADMIN/SIGNER), purpose`; email tampil readonly; submit → `completeProfile()` → `router.replace(roleHome())`. Jika `!needsOnboarding` saat mount → langsung `roleHome()`.
- `src/components/auth/GoogleSignInButton.vue`: bungkus GIS `google.accounts.id.initialize({client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID, callback})` + `renderButton` + fallback link jika script gagal load. Satu komponen dipakai Login+Register.
- `src/components/auth/TurnstileWidget.vue`: bungkus `window.turnstile.render`, expose `reset()`, emit `verified/expired/error`.

### 12.4 Router & Guard (ubah)

- `public.routes.ts`: tambah `/auth/callback` (AuthCallback), `/onboarding` (OnboardingPage, `beforeEnter: requireAuth`).
- `guards.ts`: tambah `requireOnboarding` — jika `needsOnboarding` dan target bukan `/onboarding|/logout` → redirect `/onboarding`; jika sudah complete dan target `/onboarding` → `roleHome()`. Pasang di `dashboard.routes.ts` (`/org, /signer, /admin` tambah `requireOnboarding` setelah `requireAuth`) dan di `LoginPage/RegisterPage` (user setengah onboarding yang buka `/login` → lempar ke `/onboarding`).
- `dashboard.routes.ts` tidak ubah role matrix, hanya tambah guard onboarding.

## 13. Kontrak API Final (ringkas untuk implementor)

| Method | Path | Auth | Body | Sukses |
|---|---|---|---|---|
| POST | `/auth/register` | public | `fullName,email,password,organization,phone?,role,purpose,captchaToken?` | `201 User` |
| POST | `/auth/google` | public | `{idToken}` | `200 {user,tokens,profileCompleted}` |
| PATCH | `/users/me/complete-profile` | Bearer | `fullName,organization,phone,role,purpose` | `200 User` |
| POST | `/auth/login` | public | `email,password,(captchaToken)` | `200 LoginResponse` + FE cek `user.profileCompleted` |
| GET | `/users/me` | Bearer | - | `200 User (+4 field baru)` |
| POST | `/auth/verify-email`, `/resend-verification`, `/refresh`, `/logout` | lihat `openapi.yaml:53-160` | tetap + captcha di resend | tetap |

Contoh `POST /auth/google` response:

```json
{
  "user": {"id":"...","fullName":"Sinta","email":"sinta@mail.id","organization":"","role":"SIGNER","emailVerified":true,"phone":null,"authProvider":"GOOGLE","profileCompleted":false,"avatarUrl":"https://...","createdAt":"..."},
  "tokens": {"accessToken":"...","refreshToken":"...","expiresIn":900},
  "profileCompleted": false
}
```

## 14. DoD & Perintah Verifikasi

- `cd apps/backend && pytest -q` hijau (termasuk 3 file test baru §9).
- `cd apps/frontend && npm run typecheck && npm run test:unit` hijau; tambah spec `authStore.google.spec.ts`, `TurnstileWidget.spec.ts` (mock `window.turnstile`, `window.google`).
- Manual: (a) Google baru → `/onboarding` → pilih ORG_ADMIN → `/org`; pilih SIGNER → `/signer`; (b) Google lama langsung dashboard; (c) register email tanpa captcha ditolak 400; (d) login akun Google via password → `GOOGLE_ACCOUNT_USE_SSO`; (e) refresh rotation lama tetap jalan (`test_auth.py:180-196`).
- Tidak ada secret di kode; `.env` tetap gitignored; `openapi.yaml` terupdate via PR.

## 15. Urutan Eksekusi AI (jangan paralel antar tahap)

1. BE-1: §3 migrasi Prisma + generate.
2. BE-2: §4 config + `.env.example`.
3. BE-3: §5 dua service baru.
4. BE-4: §6 schema Pydantic + `to_user_response`.
5. BE-5: §7 endpoint + §8 rate-limit/audit.
6. BE-6: §9 `openapi.yaml` + update `test_auth.py` + 3 file test baru + `pytest`.
7. FE-1: §10 env + script `index.html` + regenerate `openapi.d.ts` + `types/api.ts`.
8. FE-2: §11 service/store/composable + validators.
9. FE-3: §12 halaman/router/guard + `typecheck` + `test:unit`.
10. E2E: Playwright register-Google (mock) → onboarding → dashboard per role.
