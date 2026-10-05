import { computed } from 'vue'
import { SESSION_KEYS, sessionGet, sessionRemove, sessionSet } from '@/services/sessionStore'

function decodePayload(token: string): Record<string, unknown> | null {
  try {
    const [, payload] = token.split('.')
    if (!payload) return null
    return JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')))
  } catch {
    return null
  }
}

/** Composable JWT (FE1): baca klaim & cek kedaluwarsa tanpa verifikasi signature. */
export function useJWT() {
  const getAccessToken = () => {
    return sessionGet(SESSION_KEYS.accessToken)
  }

  const claims = computed(() => {
    const t = getAccessToken()
    return t ? decodePayload(t) : null
  })

  const isExpired = computed(() => {
    const exp = claims.value?.exp
    if (typeof exp !== 'number') return true
    return Date.now() / 1000 >= exp - 30 // 30 dtk toleransi clock-skew
  })

  function setTokens(accessToken: string, refreshToken: string) {
    sessionSet(SESSION_KEYS.accessToken, accessToken)
    sessionSet(SESSION_KEYS.refreshToken, refreshToken)
  }

  function clearTokens() {
    sessionRemove(SESSION_KEYS.accessToken)
    sessionRemove(SESSION_KEYS.refreshToken)
  }

  return { getAccessToken, claims, isExpired, setTokens, clearTokens }
}
