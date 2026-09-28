# Menjalankan SignVault — Frontend + Backend

Panduan menjalankan aplikasi secara lokal (Windows PowerShell; perintah `bash` setara untuk Linux/Mac).
Terverifikasi praktik pada 28 Sep 2026.

## 0. Prasyarat

| Kebutuhan | Versi teruji |
|---|---|
| Git | bebas |
| Node.js + npm | Node 24, npm 12 |
| Python | 3.11+ (teruji 3.14) |
| Database Postgres | Supabase (kredensial tim) — lihat Opsi B bila belum ada |

Peta port & URL:

| Layanan | URL |
|---|---|
| Backend API | `http://localhost:8000` (`/health`, `/docs`, `/api/v1/...`) |
| Frontend dev | `http://localhost:5173` |
| Storybook | `http://localhost:6006` (opsional) |

## 1. Clone & branch

```powershell
git clone https://github.com/fawwazv/SecureSign.git
cd SecureSign
git checkout develop
git pull origin develop
# Kerja fitur: git checkout -b <fe1|fe2|be>/nama-fitur   (jangan push langsung ke develop/main)
```

## 2. Backend (FastAPI)

```powershell
cd apps/backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install email-validator   # WAJIB sementara: belum ada di requirements.txt, server crash tanpa ini
python -m prisma generate --schema=../../packages/database/schema.prisma
```

### 2.1 Konfigurasi `.env`

```powershell
copy .env.example .env
# Isi di .env: DATABASE_URL, DIRECT_URL (Supabase pooler), SUPABASE_URL,
# SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, JWT_SECRET, JWT_REFRESH_SECRET, KEK_SECRET
# Generate secret: python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 2.2 Sinkron schema + seed dev

```powershell
# dari apps/backend (venv aktif)
python -m prisma db push --schema=../../packages/database/schema.prisma  # dev saja
# dari ROOT repo (tetap dengan venv backend aktif):
python packages/database/seed.py   # buat 4 user, password semua: Dev12345
```

Akun seed: `superadmin@signvault.dev`, `orgadmin@signvault.dev`,
`signer@signvault.dev`, `verifier@signvault.dev` (semua sudah terverifikasi).

### 2.3 Jalankan

```powershell
# dari apps/backend (venv aktif)
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Cek: `http://127.0.0.1:8000/health` → `{"status":"ok"}`.
Dokumentasi API: `http://127.0.0.1:8000/docs`.

### 2.4 Tes backend

```powershell
# dari apps/backend (venv aktif)
python -m pytest   # butuh DB terjangkau (testpaths = app/tests)
```

## 3. Frontend (Vue 3 + Vite)

```powershell
cd apps/frontend
copy .env.example .env   # pastikan VITE_API_BASE_URL=http://localhost:8000/api/v1
npm ci                   # instal persis package-lock.json (wajib pasca-pull/clone baru)
npx playwright install chromium   # sekali per mesin, untuk e2e
npm run dev              # http://localhost:5173
```

Perintah lain:

| Perintah | Fungsi |
|---|---|
| `npm run build` | typecheck + build produksi |
| `npm run test:unit` | Vitest |
| `npm run test:e2e` | Playwright (butuh Chromium, dev server auto-start) |
| `npm run storybook` | dokumentasi komponen (`:6006`) |

## 4. Menjalankan keduanya (alur penuh)

1. Terminal 1 — backend: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload` (dari `apps/backend`, venv aktif).
2. Terminal 2 — frontend: `npm run dev` (dari `apps/frontend`).
3. Buka `http://localhost:5173`, login dengan akun seed (mis. `orgadmin@signvault.dev` / `Dev12345`).
4. Verifikasi publik tanpa login: `http://localhost:5173/verify`.

## 5. Opsi B — database lokal sementara (bila Supabase belum ada)

Hanya untuk tes lokal, bukan staging. Memakai PGlite (Postgres in-memory via Node):

```powershell
# di folder SEMENTARA di luar repo (jangan commit)
npm init -y
npm install @electric-sql/pglite @electric-sql/pglite-socket pg
node node_modules/@electric-sql/pglite-socket/dist/scripts/server.cjs -d memory:// -p 5434 -m 20
```

Lalu di shell `apps/backend` (venv aktif), override URL (jangan ubah `.env`):

```powershell
$env:DATABASE_URL='postgresql://postgres:postgres@127.0.0.1:5434/postgres?sslmode=disable&connection_limit=1&pgbouncer=true'
$env:DIRECT_URL=$env:DATABASE_URL
python -m prisma db push --schema=../../packages/database/schema.prisma --accept-data-loss --skip-generate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Batasan yang terbukti: DB hilang saat PGlite restart (push ulang schema);
pada beban query beruntun bisa muncul error protokol driver (`prepared statement ... already exists`,
`unexpected message`) — itu keterbatasan harness, bukan bug backend. Untuk hasil definitif tetap pakai Postgres asli.

## 6. Troubleshooting

| Gejala | Penyebab & solusi |
|---|---|
| `ModuleNotFoundError: email_validator` saat start BE | `pip install email-validator` (akan ditambahkan ke requirements BE) |
| `vue-tsc` error "Cannot find module" / `vite build` gagal resolve | `node_modules` kedaluwarsa → `npm ci` ulang di `apps/frontend` |
| `playwright test` gagal (browser hilang) | `npx playwright install chromium` |
| `P1001: Can't reach database server` | `.env` masih placeholder / DB mati — cek URL, pastikan Postgres/Supabase terjangkau |
| `ModuleNotFoundError: No module named 'prisma'` (atau `fastapi`, dsb.) | venv belum aktif — traceback menunjuk `AppData\Roaming\Python\...` (Python global), bukan `.venv`. Solusi: `.\.venv\Scripts\Activate.ps1` (prompt harus berawalan `(.venv)`), lalu `pip install -r requirements.txt` + `pip install email-validator`. Wajib diulang tiap buka terminal baru |
| Port 5173/8000 bentrok | hentikan proses lama (`netstat -ano \| Select-String 5173`) atau biarkan Vite pindah port otomatis |
| Frontend 401 terus / data kosong | pastikan BE jalan dulu dan `VITE_API_BASE_URL` menunjuk ke BE yang benar |

## 7. Menghentikan server

`Ctrl+C` di tiap terminal. Background `node`/`python` yang nyangkut:
`Get-Process node,python | Select-Object ProcessName,Id,StartTime`, lalu `Stop-Process -Id <pid>`.
