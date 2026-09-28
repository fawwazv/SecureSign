import type { NavigationGuardNext, RouteLocationNormalized } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

/** Guard FE1: halaman publik auth dialihkan ke dashboard bila sudah login. */
export function guestOnly(
  _to: RouteLocationNormalized,
  _from: RouteLocationNormalized,
  next: NavigationGuardNext,
) {
  const auth = useAuthStore()
  if (auth.isAuthenticated) next(auth.needsOnboarding ? '/onboarding' : auth.roleHome())
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

/**
 * Guard onboarding (FE1-7): dipakai FE2 di /org|/signer|/admin + FE1 di /onboarding.
 * - Belum login -> /login (dengan redirect kembali).
 * - Profil belum lengkap dan target bukan /onboarding -> paksa ke /onboarding.
 * - Profil sudah lengkap dan target /onboarding -> lempar ke dashboard per role.
 */
export function requireOnboarding(
  to: RouteLocationNormalized,
  _from: RouteLocationNormalized,
  next: NavigationGuardNext,
) {
  const auth = useAuthStore()
  if (!auth.isAuthenticated) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }
  const onOnboarding = to.path === '/onboarding' || to.path.startsWith('/onboarding/')
  if (auth.needsOnboarding && !onOnboarding) {
    next('/onboarding')
    return
  }
  if (!auth.needsOnboarding && onOnboarding) {
    next(auth.roleHome())
    return
  }
  next()
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
