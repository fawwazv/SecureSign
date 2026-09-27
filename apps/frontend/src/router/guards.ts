import type { NavigationGuardNext, RouteLocationNormalized } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

/** Guard FE1: halaman publik auth dialihkan ke dashboard bila sudah login. */
export function guestOnly(
  _to: RouteLocationNormalized,
  _from: RouteLocationNormalized,
  next: NavigationGuardNext,
) {
  const auth = useAuthStore()
  if (auth.isAuthenticated) next(auth.roleHome())
  else next()
}

/** Guard umum: butuh login (dipakai FE2 untuk dashboard; disediakan FE1 di sini). */
export function requireAuth(
  to: RouteLocationNormalized,
  _from: RouteLocationNormalized,
  next: NavigationGuardNext,
) {
  const auth = useAuthStore()
  if (!auth.isAuthenticated) next({ path: '/login', query: { redirect: to.fullPath } })
  else next()
}

/** Guard role (dipakai FE2). */
export function requireRole(roles: string[]) {
  return (
    _to: RouteLocationNormalized,
    _from: RouteLocationNormalized,
    next: NavigationGuardNext,
  ) => {
    const auth = useAuthStore()
    if (!auth.isAuthenticated) return next('/login')
    if (auth.user && !roles.includes(auth.user.role)) return next('/forbidden')
    return next()
  }
}
