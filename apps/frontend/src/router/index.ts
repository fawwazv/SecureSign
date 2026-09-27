import { createRouter, createWebHistory } from 'vue-router'
import { publicRoutes } from './public.routes'

// Catatan FE1/FE2: dashboard.routes.ts dimiliki FE2.
// FE2 mendaftarkan rutenya via `router.addRoute()` dari modulnya sendiri,
// sehingga file ini tidak bergantung pada file yang belum ada.
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [...publicRoutes],
  scrollBehavior(to) {
    if (to.hash) return { el: to.hash, behavior: 'smooth' }
    return { top: 0 }
  },
})

router.afterEach((to) => {
  const title = (to.meta.title as string) || 'SignVault — Tanda Tangan Digital Aman'
  document.title = title
})

export default router
