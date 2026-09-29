# SignVault — Tanda Tangan Digital Dokumen PDF

Aplikasi tanda tangan digital dokumen PDF dengan QR verifikasi publik:
Sekretariat mengunggah PDF dan menempatkan QR, Signer menandatangani
(RSA-2048 PSS / ECDSA P-256 / Ed25519, plus PAdES untuk RSA/ECDSA),
dan siapa pun dapat memverifikasi keaslian dokumen tanpa login.

## Peran & Alur

| Peran | Akses utama |
|---|---|
| Sekretariat | Dashboard statistik, unggah PDF, atur posisi QR, minta tanda tangan, unduh PDF asli / bertanda |
| Signer | Daftar permintaan, review, tandatangani (wajib pilih key pair + jabatan opsional), unduh PDF final bertanda |
| Super Admin | Manajemen user, audit log, revoke key |
| Publik (tanpa login) | Verifikasi via upload PDF, token/QR, atau scan kamera (`/verify`) |

## Jaminan Verifikasi (`POST /api/v1/verify/upload`)

- File **bertanda (ber-QR)** yang utuh → `VALID` (beserta nama dokumen, penandatangan, jabatan, waktu).
- File **asli tanpa QR** (hash sama dengan sebelum ditandatangani) → `INVALID`
  ("QR-code tidak ada pada file ini"); halaman verifikasi menampilkan petunjuk
  mengunduh PDF bertanda dari detail dokumen.
- File yang **diubah 1 byte pun** → `INVALID` ("tidak ada tanda tangan yang cocok").
- Kunci publik tidak cocok / kunci di-revoke → `INVALID`.

> Selalu verifikasi memakai **PDF bertanda** (tombol "Unduh PDF bertanda" di
> halaman detail / halaman review signer), bukan PDF asli.

## Struktur Repo

- `apps/backend` — FastAPI (`app/api`, `app/services`, `app/crypto`, `app/tests`)
- `apps/frontend` — Vue 3 + Vite + Pinia (`src/pages`, `src/components`, `src/services`, `src/stores`)
- `packages/database` — skema Prisma + `seed.py` (akun dev)
- `docs/api-docs/openapi.yaml` — kontrak API (sumber regenerasi `src/types/openapi.d.ts`)

## Menjalankan

Panduan lengkap: [`running.md`](running.md).

```powershell
# Backend (dari apps/backend, venv aktif)
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Frontend (dari apps/frontend)
npm run dev
```

Seed akun dev: `python packages/database/seed.py` (dari root repo).

## Uji Otomatis

```powershell
# Backend (dari apps/backend)
python -m pytest app/tests/test_documents.py app/tests/test_verify.py -q

# Frontend (dari apps/frontend)
npm run test:unit -- --run
npx vue-tsc --noEmit -p tsconfig.json
```
