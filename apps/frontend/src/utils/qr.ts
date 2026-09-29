/**
 * Helper parsing QR untuk halaman verifikasi publik (FE1).
 * QR SignVault berisi: token mentah, URL verifikasi, ATAU JSON publik
 * {v,doc,sig,name,pos,org,at,alg,url} — ketiganya dinormalisasi di sini
 * agar mudah di-unit-test tanpa kamera.
 */
export interface QrPayloadInfo {
  sigId: string
  url: string
  name?: string
  position?: string
  org?: string
  signedAt?: string
  algorithm?: string
  documentId?: string
}

export function parseQrPayload(text: string): QrPayloadInfo | null {
  const t = text.trim()
  if (!t.startsWith('{')) return null
  try {
    const d = JSON.parse(t) as Record<string, unknown>
    if (d.v !== 1 || typeof d.sig !== 'string') return null
    const info: QrPayloadInfo = {
      sigId: d.sig,
      url: typeof d.url === 'string' && d.url ? d.url : '',
    }
    if (typeof d.name === 'string') info.name = d.name
    if (typeof d.pos === 'string') info.position = d.pos
    if (typeof d.org === 'string') info.org = d.org
    if (typeof d.at === 'string') info.signedAt = d.at
    if (typeof d.alg === 'string') info.algorithm = d.alg
    if (typeof d.doc === 'string') info.documentId = d.doc
    return info
  } catch {
    return null
  }
}

/** URL verifikasi dari payload apapun (JSON -> field url, selain itu mentah). */
export function extractVerifyUrl(text: string): string {
  const info = parseQrPayload(text)
  if (info?.url) return info.url
  return text.trim()
}

export function extractTokenFromQrText(text: string): string {
  const t = text.trim()
  if (!t) return ''
  const info = parseQrPayload(t)
  if (info) return info.sigId
  try {
    const url = new URL(t)
    const pathMatch = url.pathname.match(/\/verify\/([^\/?#]+)/)
    if (pathMatch?.[1]) return decodeURIComponent(pathMatch[1])
    const q = url.searchParams.get('token')
    if (q) return q
    return t
  } catch {
    return t
  }
}

/**
 * Pemindai kamera didukung di semua browser modern yang punya
 * `navigator.mediaDevices.getUserMedia` (Chrome, Edge, Firefox, Safari 11+).
 * Dekode QR memakai `html5-qrcode` (berbasis WebAssembly/canvas), bukan
 * `BarcodeDetector` yang hanya ada di Chromium — agar kompatibel lintas browser.
 */
export function isCameraQrSupported(): boolean {
  try {
    return (
      typeof window !== 'undefined' &&
      typeof navigator !== 'undefined' &&
      !!navigator.mediaDevices?.getUserMedia &&
      typeof window.isSecureContext !== 'undefined' &&
      (window.isSecureContext || window.location.hostname === 'localhost')
    )
  } catch {
    return false
  }
}
