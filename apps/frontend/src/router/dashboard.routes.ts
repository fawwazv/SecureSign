import type { Router } from 'vue-router'
import { requireAuth, requireRole } from './guards'

/**
 * Rute dashboard FE2. Didaftarkan via `router.addRoute()` agar
 * `router/index.ts` (milik FE1) tidak perlu diubah.
 *
 * Dipanggil sekali dari entry FE2 (lihat Tahap 2), mis. di main.ts
 * milik FE2 atau modul bootstrap dashboard.
 */
export function registerDashboardRoutes(router: Router): void {
  const orgOnly = requireRole(['SEKRETARIAT', 'SUPER_ADMIN'])
  const signerOnly = requireRole(['SIGNER', 'SUPER_ADMIN'])
  const superOnly = requireRole(['SUPER_ADMIN'])

  router.addRoute({
    path: '/org',
    component: () => import('@/layouts/DashboardLayout.vue'),
    beforeEnter: requireAuth,
    children: [
      {
        path: '',
        name: 'org-dashboard',
        component: () => import('@/pages/org/Dashboard.vue'),
        beforeEnter: orgOnly,
        meta: { title: 'Dokumen Saya — SignVault' },
      },
      {
        path: 'upload',
        name: 'org-upload',
        component: () => import('@/pages/org/Upload.vue'),
        beforeEnter: orgOnly,
        meta: { title: 'Upload PDF — SignVault' },
      },
      {
        path: 'documents/:id',
        name: 'org-document-detail',
        component: () => import('@/pages/org/DocumentDetail.vue'),
        beforeEnter: orgOnly,
        meta: { title: 'Detail Dokumen — SignVault' },
      },
    ],
  })

  router.addRoute({
    path: '/signer',
    component: () => import('@/layouts/DashboardLayout.vue'),
    beforeEnter: requireAuth,
    children: [
      {
        path: '',
        name: 'signer-dashboard',
        component: () => import('@/pages/signer/Dashboard.vue'),
        beforeEnter: signerOnly,
        meta: { title: 'Permintaan Tanda Tangan — SignVault' },
      },
      {
        path: 'batch',
        name: 'signer-batch',
        component: () => import('@/pages/signer/BatchSign.vue'),
        beforeEnter: signerOnly,
        meta: { title: 'Batch Signing — SignVault' },
      },
      {
        path: 'requests/:id',
        name: 'signer-request-detail',
        component: () => import('@/pages/signer/SignRequestDetail.vue'),
        beforeEnter: signerOnly,
        meta: { title: 'Detail Permintaan — SignVault' },
      },
    ],
  })

  router.addRoute({
    path: '/admin',
    component: () => import('@/layouts/DashboardLayout.vue'),
    beforeEnter: requireAuth,
    children: [
      {
        path: '',
        name: 'admin-dashboard',
        component: () => import('@/pages/admin/Dashboard.vue'),
        beforeEnter: superOnly,
        meta: { title: 'Ringkasan Platform — SignVault' },
      },
      {
        path: 'users',
        name: 'admin-users',
        component: () => import('@/pages/admin/Users.vue'),
        beforeEnter: superOnly,
        meta: { title: 'Manajemen User — SignVault' },
      },
      {
        path: 'audit',
        name: 'admin-audit',
        component: () => import('@/pages/admin/AuditLog.vue'),
        beforeEnter: superOnly,
        meta: { title: 'Audit Log — SignVault' },
      },
    ],
  })
}
