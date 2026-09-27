import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import type { ApiErrorBody, LoginResponse } from '@/types/api'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

type RetriableConfig = InternalAxiosRequestConfig & { _retry?: boolean }

function getAccessToken(): string | null {
  try {
    return localStorage.getItem('sv:access_token')
  } catch {
    return null
  }
}

function getRefreshToken(): string | null {
  try {
    return localStorage.getItem('sv:refresh_token')
  } catch {
    return null
  }
}

function persistSession(resp: LoginResponse) {
  localStorage.setItem('sv:access_token', resp.tokens.accessToken)
  localStorage.setItem('sv:refresh_token', resp.tokens.refreshToken)
  localStorage.setItem('sv:user', JSON.stringify(resp.user))
}

function clearSession() {
  try {
    localStorage.removeItem('sv:access_token')
    localStorage.removeItem('sv:refresh_token')
    localStorage.removeItem('sv:user')
  } catch {
    /* abaikan */
  }
}

// Single-flight: banyak request 401 bersamaan hanya memicu 1x refresh.
let refreshPromise: Promise<LoginResponse> | null = null

function refreshTokens(): Promise<LoginResponse> {
  if (!refreshPromise) {
    const rt = getRefreshToken()
    if (!rt) return Promise.reject(new Error('no-refresh-token'))
    // axios polos (tanpa interceptor) agar tidak rekursi.
    refreshPromise = axios
      .post<LoginResponse>(`${apiClient.defaults.baseURL}/auth/refresh`, { refreshToken: rt }, {
        timeout: 15000,
        headers: { 'Content-Type': 'application/json' },
      })
      .then((r) => r.data)
      .finally(() => {
        refreshPromise = null
      })
  }
  return refreshPromise
}

function isAuthFlow(url: string): boolean {
  return url.includes('/auth/login') || url.includes('/auth/refresh')
}

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

apiClient.interceptors.response.use(
  (res) => res,
  async (error: AxiosError<ApiErrorBody>) => {
    const original = error.config as RetriableConfig | undefined
    const status = error.response?.status
    const url = original?.url ?? ''

    // 401 sekali → coba silent refresh (ikut rotasi BE), lalu ulangi request.
    if (status === 401 && original && !original._retry && !isAuthFlow(url)) {
      original._retry = true
      try {
        const resp = await refreshTokens()
        persistSession(resp)
        original.headers.Authorization = `Bearer ${resp.tokens.accessToken}`
        return apiClient(original)
      } catch {
        /* lanjut ke logout di bawah */
      }
    }

    if (status === 401 && !isAuthFlow(url)) {
      clearSession()
      if (window.location.pathname !== '/login') window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

export function toApiMessage(err: unknown, fallback: string): string {
  if (axios.isAxiosError<ApiErrorBody>(err)) {
    return err.response?.data?.error?.message ?? err.message ?? fallback
  }
  return fallback
}

/** Kode error kontrak BE (`error.code`), cth. EMAIL_TAKEN, EMAIL_NOT_VERIFIED. */
export function toApiCode(err: unknown): string | undefined {
  if (axios.isAxiosError<ApiErrorBody>(err)) {
    return err.response?.data?.error?.code
  }
  return undefined
}
