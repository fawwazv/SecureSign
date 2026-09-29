# Panduan Staging — SignVault Backend

Deploy native via Uvicorn, **tanpa Docker** (PRD §15). Berlaku untuk VM
(Ubuntu/Debian) maupun simulasi staging lokal.

## 1. Simulasi staging lokal (wajib lolos sebelum klaim "siap staging")

```bash
cd apps/backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# terminal lain:
set ENV=staging&& python scripts/smoke.py   # Windows
# ENV=staging python scripts/smoke.py       # Linux/Mac
```
Harus keluar `SMOKE: LOLOS`. Script memakai DB yang sama dengan `.env`;
data smoke dibersihkan otomatis.

## 2. Deploy ke VM staging

1. Python 3.11+, Node 18+, `git clone`, checkout `develop`.
2. `cd apps/backend && pip install -r requirements.txt`
3. `copy .env.example .env` → isi semua nilai staging (DB/Supabase/JWT/KEK
   bedakan dari dev; SMTP isi bila mau email betulan).
4. `cd ../../packages/database && npm install && npx prisma db push && python -m prisma generate`
5. Jalankan sebagai service (contoh systemd):
   ```ini
   [Unit]
   Description=SignVault Backend
   After=network.target
   [Service]
   WorkingDirectory=/srv/signvault/apps/backend
   EnvironmentFile=/srv/signvault/apps/backend/.env
   ExecStart=/srv/signvault/apps/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
   Restart=always
   [Install]
   WantedBy=multi-user.target
   ```
6. Reverse proxy (nginx) + TLS 1.3 di depan Uvicorn; buka hanya port 443.
7. Dari mesin apa pun: `API_BASE_URL=https://staging-API-Anda ENV=staging python scripts/smoke.py`

## 3. Cegah secret bocor (PRD §16)

Jangan pernah commit file `.env` (sudah gitignored). Sebelum push, pastikan
`git status` tidak menampilkan file `.env`.
