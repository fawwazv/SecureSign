# SignVault Backend — Quickstart (5–10 menit dari fresh clone)

Prasyarat: Python 3.11+, Node 18+ (untuk Prisma CLI), akses Supabase project.

## 1. Install dependency
```bash
cd apps/backend
pip install -r requirements.txt
```

## 2. Siapkan env
```bash
copy .env.example .env   # Windows
# cp .env.example .env   # Linux/Mac
```
Isi `.env`: `DATABASE_URL`, `DIRECT_URL`, `SUPABASE_*`, `JWT_SECRET`,
`JWT_REFRESH_SECRET`, `KEK_SECRET` (generate: `python -c "import secrets; print(secrets.token_urlsafe(48))"`),
sisanya boleh default. `.env` **jangan dicommit** (sudah gitignored).

## 3. Database
```bash
cd ../../packages/database
npm install
npx prisma db push        # sinkronkan schema ke Supabase
python -m prisma generate # generate Prisma Client Python
python seed.py            # 4 user dev (password: Dev12345)
```

## 4. Jalan
```bash
cd ../../apps/backend
python -m uvicorn app.main:app --reload --port 8000
```
Cek: http://localhost:8000/health → `{"status":"ok"}`,
Swagger: http://localhost:8000/docs

## 5. Test
```bash
python -m pytest app/tests/test_foundation.py app/tests/test_email.py -q  # cepat (<30 dtk)
python -m pytest app/tests/test_auth.py -q        # ~1,5 mnt
python -m pytest app/tests/test_crypto.py -q      # ~1 mnt
python -m pytest app/tests/test_documents.py -q   # ~1,5 mnt
python -m pytest app/tests/test_signing.py -q     # ~3 mnt
python -m pytest app/tests/test_verify.py -q      # ~5 mnt
```
Jalankan **per-file** (jangan sekaligus — suite penuh >10 menit via pooler jauh).

## Lint & format
```bash
python -m ruff check app/ && python -m black --check app/
```

## Simulasi staging lokal
```bash
set ENV=staging&& python scripts/smoke.py  # Windows
# ENV=staging python scripts/smoke.py      # Linux/Mac
```
Butuh backend jalan di port 8000. Lihat `docs/deployment/staging.md`.
