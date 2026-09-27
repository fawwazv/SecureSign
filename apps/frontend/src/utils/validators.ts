export function isEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(value.trim())
}

export function isStrongPassword(value: string): boolean {
  // Min 8 karakter, ada huruf + angka (aturan MVP, Argon2id di sisi server).
  return value.length >= 8 && /[A-Za-z]/.test(value) && /\d/.test(value)
}

export const validators = {
  required: (v: string) => v.trim().length > 0,
  email: isEmail,
  password: isStrongPassword,
  minLength: (v: string, n: number) => v.trim().length >= n,
}

export function registerErrorMessage(code?: string): string {
  switch (code) {
    case 'EMAIL_TAKEN':
    case 'EMAIL_EXISTS':
      return 'Email sudah terdaftar. Silakan login atau gunakan email lain.'
    case 'WEAK_PASSWORD':
      return 'Kata sandi minimal 8 karakter dan mengandung huruf + angka.'
    case 'INVALID_PAYLOAD':
      return 'Data registrasi tidak valid. Periksa kembali isian formulir.'
    default:
      return 'Registrasi gagal. Coba lagi dalam beberapa saat.'
  }
}

export function loginErrorMessage(code?: string, fallback?: string): string {
  switch (code) {
    case 'INVALID_CREDENTIALS':
      return 'Email atau kata sandi salah.'
    case 'EMAIL_NOT_VERIFIED':
      return 'Email belum terverifikasi. Cek kotak masuk atau kirim ulang verifikasi.'
    case 'FEATURE_UNAVAILABLE':
      return 'Fitur ini belum tersedia di backend.'
    default:
      return fallback ?? 'Gagal masuk. Coba lagi dalam beberapa saat.'
  }
}
