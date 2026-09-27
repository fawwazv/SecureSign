/**
 * Tipe hasil generate dari `docs/api-docs/openapi.yaml` (openapi-typescript).
 *
 * Catatan FE1: file ini adalah stub yang mengikuti kontrak PRD utama §10
 * (versioning /api/v1, error { error: { code, message } }, pagination).
 * Setelah BE menerbitkan openapi.yaml, jalankan:
 *   npx openapi-typescript ../../docs/api-docs/openapi.yaml -o src/types/api.ts
 * dan ganti isi file ini dengan output generator.
 */

export type Role = 'SUPER_ADMIN' | 'ORG_ADMIN' | 'SIGNER' | 'VERIFIER'

export interface ApiErrorBody {
  error: {
    code: string
    message: string
  }
}

export interface Paginated<T> {
  data: T[]
  page: number
  limit: number
  total: number
}

export interface User {
  id: string
  fullName: string
  email: string
  organization: string
  role: Role
  emailVerified: boolean
  createdAt: string
}

export interface AuthTokens {
  accessToken: string
  refreshToken: string
  expiresIn: number
}

export interface RegisterPayload {
  fullName: string
  email: string
  password: string
  organization: string
  role: Extract<Role, 'ORG_ADMIN' | 'SIGNER'>
  purpose: string
}

export interface LoginPayload {
  email: string
  password: string
}

export interface VerifyResult {
  status: 'VALID' | 'INVALID'
  documentName?: string
  signerName?: string
  signedAt?: string
  reason?: string
  auditTrail?: Array<{ event: string; at: string; actor?: string }>
}

export interface paths {
  '/auth/register': {
    post: {
      requestBody: { content: { 'application/json': RegisterPayload } }
      responses: { 201: { content: { 'application/json': User } } }
    }
  }
  '/auth/login': {
    post: {
      requestBody: { content: { 'application/json': LoginPayload } }
      responses: { 200: { content: { 'application/json': { user: User; tokens: AuthTokens } } } }
    }
  }
}
