/**
 * Helper parsing QR untuk halaman verifikasi publik (FE1).
 * QR SignVault berisi token mentah ATAU URL verifikasi —
 * dua format itu dinormalisasi ke token murni di sini agar
 * mudah di-unit-test tanpa kamera.
 */
export function extractTokenFromQrText(text: string): string {
  const t = text.trim()
  if (!t) return ''
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
