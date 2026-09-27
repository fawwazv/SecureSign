import type { RouteRecordRaw } from 'vue-router'
import LandingLayout from '@/layouts/LandingLayout.vue'
import { guestOnly } from './guards'

/** Rute publik milik FE1: landing, auth, verifikasi email, verifikasi publik. */
export const publicRoutes: RouteRecordRaw[] = [
  {
    path: '/',
    component: LandingLayout,
    children: [
      {
        path: '',
        name: 'landing',
        component: () => import('@/pages/public/LandingPage.vue'),
      },
      {
        path: 'login',
        name: 'login',
        beforeEnter: guestOnly,
        component: () => import('@/pages/public/LoginPage.vue'),
        meta: { title: 'Masuk — SignVault' },
      },
      {
        path: 'register',
        name: 'register',
        beforeEnter: guestOnly,
        component: () => import('@/pages/public/RegisterPage.vue'),
        meta: { title: 'Daftar — SignVault' },
      },
      {
        path: 'forgot-password',
        name: 'forgot-password',
        beforeEnter: guestOnly,
        component: () => import('@/pages/public/ForgotPasswordPage.vue'),
        meta: { title: 'Lupa Kata Sandi — SignVault' },
      },
      {
        path: 'verify-email',
        name: 'verify-email',
        component: () => import('@/pages/public/VerifyEmailPage.vue'),
        meta: { title: 'Verifikasi Email — SignVault' },
      },
      {
        path: 'verify',
        name: 'verify',
        component: () => import('@/pages/public/VerifyPage.vue'),
        meta: { title: 'Verifikasi Dokumen — SignVault' },
      },
      {
        path: 'forbidden',
        name: 'forbidden',
        component: () => import('@/pages/public/ForbiddenPage.vue'),
        meta: { title: 'Akses Ditolak — SignVault' },
      },
    ],
  },
]
