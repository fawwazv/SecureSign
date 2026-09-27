import { computed } from 'vue'

const ACCESS_KEY = 'sv:access_token'
const REFRESH_KEY = 'sv:refresh_token'

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
    try {
      return localStorage.getItem(ACCESS_KEY)
    } catch {
      return null
    }
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
    localStorage.setItem(ACCESS_KEY, accessToken)
    localStorage.setItem(REFRESH_KEY, refreshToken)
  }

  function clearTokens() {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
  }

  return { getAccessToken, claims, isExpired, setTokens, clearTokens }
}
