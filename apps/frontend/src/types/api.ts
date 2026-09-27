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

export type User = components['schemas']['User']
export type AuthTokens = components['schemas']['AuthTokens']
export type LoginResponse = components['schemas']['LoginResponse']
export type RegisterPayload = components['schemas']['RegisterRequest']
export type LoginPayload = components['schemas']['LoginRequest']
export type VerifyEmailPayload = components['schemas']['VerifyEmailRequest']

export type DocumentStatus = components['schemas']['DocumentStatus']
export type VerifyResult = components['schemas']['VerifyResult']
