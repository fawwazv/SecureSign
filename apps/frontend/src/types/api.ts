/**
 * Tipe kontrak API SignVault — dihasilkan dari `docs/api-docs/openapi.yaml`.
 *
 * - `openapi.d.ts`: output murni `openapi-typescript` (JANGAN edit manual).
 *   Regenerate: `npx openapi-typescript ../../docs/api-docs/openapi.yaml -o src/types/openapi.d.ts`
 * - File ini: alias domain FE1 di atas skema generate agar service/halaman
 *   memakai nama stabil. Sync dengan kontrak: openapi v0.1.0.
 */
import type { components, paths } from './openapi'

export type { paths }
export type Schemas = components['schemas']

export type Role = components['schemas']['Role']
export type ApiErrorBody = components['schemas']['ErrorBody']
export type MessageResponse = components['schemas']['MessageResponse']

export interface Paginated<T> {
  data: T[]
  page: number
  limit: number
  total: number
}

export type User = components['schemas']['User'] & {
  /** FE1-2 forward-compat: diisi BE setelah migrasi OAuth (nullable/optional sampai openapi diregen). */
  phone?: string | null
  authProvider?: 'EMAIL' | 'GOOGLE'
  profileCompleted?: boolean
  avatarUrl?: string | null
}
export type AuthTokens = components['schemas']['AuthTokens']
export type LoginResponse = components['schemas']['LoginResponse']
export type RegisterPayload = components['schemas']['RegisterRequest'] & {
  /** FE1-2: field baru Skenario 2 (opsional sampai BE wajibkan). */
  phone?: string
  captchaToken?: string
}
export type LoginPayload = components['schemas']['LoginRequest'] & {
  captchaToken?: string
}
export type VerifyEmailPayload = components['schemas']['VerifyEmailRequest']

/** FE1-2: payload login Google (POST /auth/google {idToken}). */
export interface GoogleLoginPayload {
  idToken: string
}

/** FE1-2: payload onboarding (PATCH /users/me/complete-profile). */
export interface CompleteProfilePayload {
  fullName: string
  organization: string
  phone: string
  role: Extract<Role, 'ORG_ADMIN' | 'SIGNER'>
  purpose: string
}

/** FE1-2: response login Google = LoginResponse + flag onboarding. */
export interface GoogleLoginResponse {
  user: User
  tokens: AuthTokens
  profileCompleted: boolean
}

export type DocumentStatus = components['schemas']['DocumentStatus']
export type VerifyResult = components['schemas']['VerifyResult']
