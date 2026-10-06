# SignVault — Tanda Tangan Digital Dokumen PDF

## Deskripsi

SignVault adalah aplikasi tanda tangan digital untuk dokumen PDF dengan QR
verifikasi publik. Sekretariat mengunggah PDF dan menempatkan QR, Signer
menandatangani (RSA-2048 PSS / ECDSA P-256 / Ed25519, plus PAdES untuk
RSA/ECDSA), dan siapa pun dapat memverifikasi keaslian dokumen tanpa login
melalui halaman `/verify` (upload PDF, token/QR, file + kunci, atau scan kamera).

| Peran | Akses utama |
|---|---|
| Sekretariat | Dashboard statistik, unggah PDF, atur posisi QR, minta tanda tangan, unduh PDF asli / bertanda |
| Signer | Daftar permintaan, review, tandatangani (pilih key pair + jabatan opsional), unduh PDF final bertanda |
| Super Admin | Manajemen user, audit log, revoke key |
| Publik (tanpa login) | Verifikasi dokumen + uji performa sign/verify |

## Cara Instalasi

Prasyarat: Git, Node.js 24 + npm 12, Python 3.11+, database PostgreSQL
(Supabase — kredensial tim), dan file `.env` yang sudah diisi
(lihat `apps/backend/.env.example`).

```powershell
# 1. Clone repo
git clone https://github.com/fawwazv/SecureSign.git
cd SecureSign

# 2. Backend (dari apps/backend, venv aktif)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install email-validator
python -m prisma generate --schema=../../packages/database/schema.prisma
copy .env.example .env   # lalu isi kredensial + secret
python -m prisma db push --schema=../../packages/database/schema.prisma

# 3. Seed akun dev (dari root repo, password semua: Dev12345)
python packages/database/seed.py

# 4. Frontend (dari apps/frontend)
copy .env.example .env   # pastikan VITE_API_BASE_URL=http://localhost:8000/api/v1
npm ci
```

## Cara Menjalankan

```powershell
# Terminal 1 — backend (dari apps/backend, venv aktif)
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2 — frontend (dari apps/frontend)
npm run dev
```

Buka `http://localhost:5173`, login dengan akun seed
(mis. `orgadmin@signvault.dev` / `Dev12345`).
Kesehatan API: `http://127.0.0.1:8000/health` → `{"status":"ok"}`.
Dokumentasi API: `http://127.0.0.1:8000/docs`.
Panduan lengkap dan troubleshooting: [`running.md`](running.md).

## Contoh Penggunaan

1. **Sekretariat** login → Dashboard → **Unggah Dokumen** (PDF) → geser
   kotak QR ke posisi yang diinginkan → **Saya sudah yakin** → **Minta tanda
   tangan** (pilih Signer).
2. **Signer** login → **Permintaan Tanda Tangan** → Review → pilih key pair,
   isi Jabatan (mis. "Kaprodi") → **Tandatangani** → salin token/ID dan kunci
   publik bila perlu.
3. **Verifikasi publik** tanpa login di `/verify`:
   - *Upload PDF*: unggah PDF final bertanda → `VALID` (file asli tanpa QR
     atau file yang diubah 1 byte → `TIDAK VALID`).
   - *File + Kunci*: unggah PDF bertanda + tempel kunci publik → kunci benar
     `VALID`, kunci lain `TIDAK VALID` (demo uji kunci salah).
   - *Uji Performa*: unggah PDF, atur iterasi (min. 30) → tabel rata-rata /
     tercepat / terlambat operasi Sign dan Verifikasi.

## Uji Otomatis

```powershell
# Backend (dari apps/backend)
python -m pytest app/tests/test_documents.py app/tests/test_verify.py -q

# Frontend (dari apps/frontend)
npm run test:unit -- --run
npx vue-tsc --noEmit -p tsconfig.json
```

## Anggota Kelompok

| Nama | NPM |
|---|---|
| Farizal Muztahidin | 247006111044 |
| Muhammad Fawwazul Haq | 247006111088 |
| Muhammad Alif Akhdan Tsani | 247006111166 |
