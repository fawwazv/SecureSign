import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import type { ApiErrorBody } from '@/types/api'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

function getAccessToken(): string | null {
  try {
    return localStorage.getItem('sv:access_token')
  } catch {
    return null
  }
}

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

apiClient.interceptors.response.use(
  (res) => res,
  async (error: AxiosError<ApiErrorBody>) => {
    const status = error.response?.status
    if (status === 401 && !error.config?.url?.includes('/auth/')) {
      try {
        localStorage.removeItem('sv:access_token')
        localStorage.removeItem('sv:refresh_token')
        localStorage.removeItem('sv:user')
      } catch {
        /* abaikan */
      }
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
