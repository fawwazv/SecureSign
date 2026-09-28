export function isEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(value.trim())
}

export function isStrongPassword(value: string): boolean {
  // Min 8 karakter, ada huruf + angka (aturan MVP, Argon2id di sisi server).
  return value.length >= 8 && /[A-Za-z]/.test(value) && /\d/.test(value)
}

export function isPhone(value: string): boolean {
  // FE1-4: +62/08, min 7 digit, toleransi spasi/strip/kurung.
  return /^[+0-9][0-9\s\-()]{6,19}$/.test(value.trim())
}

export const validators = {
  required: (v: string) => v.trim().length > 0,
  email: isEmail,
  password: isStrongPassword,
  phone: isPhone,
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
    case 'CAPTCHA_FAILED':
      return 'Verifikasi CAPTCHA gagal. Muat ulang CAPTCHA dan coba lagi.'
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
    case 'GOOGLE_ACCOUNT_USE_SSO':
      return 'Akun ini memakai Login Google. Lanjutkan dengan tombol Google.'
    case 'GOOGLE_VERIFY_FAILED':
      return 'Verifikasi Google gagal. Coba lagi.'
    case 'INVALID_GOOGLE_SUBJECT':
      return 'Akun Google tidak cocok. Gunakan akun yang sama seperti saat daftar.'
    case 'CAPTCHA_FAILED':
      return 'Verifikasi CAPTCHA gagal. Muat ulang CAPTCHA dan coba lagi.'
    case 'FEATURE_UNAVAILABLE':
      return 'Fitur ini belum tersedia di backend.'
    default:
      return fallback ?? 'Gagal masuk. Coba lagi dalam beberapa saat.'
  }
}
