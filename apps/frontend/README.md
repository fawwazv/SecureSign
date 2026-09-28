# SignVault — Frontend (FE1: Public Pages & Design System)

## Menjalankan

```bash
cd apps/frontend
cp .env.example .env   # sesuaikan VITE_API_BASE_URL
npm install
npm run dev            # http://localhost:5173
```

> Wajib setelah pull/clone baru: sinkronkan dependensi + browser e2e.
> Gejala bila dilewati: `vue-tsc` error "Cannot find module",
> `vite build` gagal resolve dep, `playwright test` gagal (browser hilang).
>
> ```bash
> cd apps/frontend
> npm ci                         # instal persis package-lock.json (atau npm install)
> npx playwright install chromium  # browser e2e (sekali per mesin)
> ```

## Skrip

| Skrip | Fungsi |
|---|---|
| `npm run dev` | Vite dev server |
| `npm run build` | Typecheck + build produksi |
| `npm run test:unit` | Vitest (validator, formatDate) |
| `npm run test:e2e` | Playwright (landing, register, verify) |

## Cakupan FE1

- `src/components/ui/**` — Button, Input, Card, Badge, Alert, Modal, Table, Tabs (token `design.md`).
- `src/pages/public/**` — Landing, Login, Register (6 field), ForgotPassword, VerifyEmail, Verify, Forbidden.
- `src/layouts/LandingLayout.vue` — header transparan-sticky + footer deep-blue.
- `src/router/{index,public.routes,guards}.ts`, `src/stores/{authStore,notificationStore}.ts`,
  `src/composables/{useAuth,useJWT}.ts`, `src/services/{apiClient,authService}.ts`,
  `src/utils/**`, `src/types/api.ts` (stub → generate via `openapi-typescript` setelah BE rilis `openapi.yaml`).

Generate tipe dari OpenAPI:

```bash
npx openapi-typescript ../../docs/api-docs/openapi.yaml -o src/types/api.ts
```
