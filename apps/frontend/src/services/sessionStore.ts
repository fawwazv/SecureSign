/**
 * Penyimpanan sesi per-tab (sessionStorage).
 *
 * Setiap tab/window browser punya sesi independen: tab baru tampil sebagai
 * guest (landing), refresh tetap login, tutup tab = keluar. Berbeda dengan
 * localStorage yang dipakai bersama semua tab (satu tab logout/refresh
 * bisa menendang tab lain, dan tab baru ikut login akun tab lama).
 */
export const SESSION_KEYS = {
  accessToken: 'sv:access_token',
  refreshToken: 'sv:refresh_token',
  user: 'sv:user',
  googleCredential: 'sv:google_credential',
} as const

function storage(): Storage | null {
  try {
    if (typeof sessionStorage === 'undefined') return null
    return sessionStorage
  } catch {
    return null
  }
}

export function sessionGet(key: string): string | null {
  try {
    return storage()?.getItem(key) ?? null
  } catch {
    return null
  }
}

export function sessionSet(key: string, value: string): void {
  try {
    storage()?.setItem(key, value)
  } catch {
    /* abaikan (mode privat / storage penuh) */
  }
}

export function sessionRemove(key: string): void {
  try {
    storage()?.removeItem(key)
  } catch {
    /* abaikan */
  }
}

export function sessionClearAuth(): void {
  sessionRemove(SESSION_KEYS.accessToken)
  sessionRemove(SESSION_KEYS.refreshToken)
  sessionRemove(SESSION_KEYS.user)
  sessionRemove(SESSION_KEYS.googleCredential)
}
