import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import type { ApiErrorBody, LoginResponse } from '@/types/api'
import { SESSION_KEYS, sessionClearAuth, sessionGet, sessionSet } from './sessionStore'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

type RetriableConfig = InternalAxiosRequestConfig & { _retry?: boolean }

function getAccessToken(): string | null {
  return sessionGet(SESSION_KEYS.accessToken)
}

function getRefreshToken(): string | null {
  return sessionGet(SESSION_KEYS.refreshToken)
}

function persistSession(resp: LoginResponse) {
  sessionSet(SESSION_KEYS.accessToken, resp.tokens.accessToken)
  sessionSet(SESSION_KEYS.refreshToken, resp.tokens.refreshToken)
  sessionSet(SESSION_KEYS.user, JSON.stringify(resp.user))
}

function clearSession() {
  sessionClearAuth()
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
      // Token mungkin sudah disegarkan alur lain di tab ini (mis. retry
      // beruntun): jangan refresh ulang bila token kini sudah berbeda.
      const sentAuth = String(original.headers?.Authorization ?? '')
      const current = getAccessToken()
      if (current && sentAuth !== `Bearer ${current}`) {
        original.headers.Authorization = `Bearer ${current}`
        return apiClient(original)
      }
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
    const data = err.response?.data as ApiErrorBody | Blob | undefined
    // Respons JSON normal: { error: { message } }.
    if (data && !(data instanceof Blob)) {
      return data?.error?.message ?? err.message ?? fallback
    }
    // Respons Blob (unduhan PDF): body JSON tidak ter-parse otomatis.
    return err.message ?? fallback
  }
  return fallback
}

/** Badan error JSON yang tersembunyi di balik respons Blob (unduhan PDF). */
async function parseBlobErrorBody(data: unknown): Promise<ApiErrorBody | null> {
  try {
    if (data instanceof Blob) {
      const text = await data.text()
      if (!text) return null
      const parsed = JSON.parse(text) as ApiErrorBody
      if (parsed && typeof parsed === 'object' && 'error' in parsed) return parsed
      return null
    }
  } catch {
    /* abaikan — pemanggil pakai fallback */
  }
  return null
}

/** Versi async dari toApiMessage yang mampu membaca body error berbentuk Blob. */
export async function toApiMessageAsync(err: unknown, fallback: string): Promise<string> {
  if (axios.isAxiosError<ApiErrorBody>(err)) {
    const data = err.response?.data as ApiErrorBody | Blob | undefined
    if (data instanceof Blob) {
      const parsed = await parseBlobErrorBody(data)
      return parsed?.error?.message ?? fallback
    }
    return data?.error?.message ?? err.message ?? fallback
  }
  return fallback
}

/** Kode error kontrak BE (`error.code`), cth. EMAIL_TAKEN, EMAIL_NOT_VERIFIED. */
export function toApiCode(err: unknown): string | undefined {
  if (axios.isAxiosError<ApiErrorBody>(err)) {
    const data = err.response?.data as ApiErrorBody | Blob | undefined
    if (data && !(data instanceof Blob)) return data?.error?.code
    return undefined
  }
  return undefined
}

/** Versi async dari toApiCode yang mampu membaca body error berbentuk Blob. */
export async function toApiCodeAsync(err: unknown): Promise<string | undefined> {
  if (axios.isAxiosError<ApiErrorBody>(err)) {
    const data = err.response?.data as ApiErrorBody | Blob | undefined
    if (data instanceof Blob) {
      const parsed = await parseBlobErrorBody(data)
      return parsed?.error?.code
    }
    if (data && typeof data === 'object') return data?.error?.code
    return undefined
  }
  return undefined
}
