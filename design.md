# DESIGN SYSTEM — SignVault

**Versi:** 1.1
**Untuk:** Frontend Developer (FE1 & FE2)
**Tidak untuk:** Backend Developer

---

## 1. Prinsip Desain

- **Clean & Professional** — Dominan putih, aksen warna terbatas.
- **Trustworthy** — Biru tua sebagai warna utama (kepercayaan).
- **Friendly** — Sentuhan krem dan coklat untuk kehangatan.
- **Accessible** — Kontras minimal 4.5:1 untuk teks.

---

## 2. Palet Warna

| Nama | Hex | Tailwind Token | Penggunaan |
|---|---|---|---|
| White | `#FFFFFF` | `white` | Background utama, card. |
| Cream | `#FFF1E7` | `cream` | Background section, card highlight, hover. |
| Light Blue | `#B5D2E6` | `light-blue` | Secondary button, tag, info background. |
| Deep Blue | `#326080` | `deep-blue` | Primary button, link, active nav, header. |
| Brown | `#805232` | `brown` | Accent, warning, secondary CTA, badge signer. |

### Contoh Penggunaan

| Elemen | Ketentuan |
|---|---|
| Primary Button | bg `#326080`, teks putih, hover `#28506A`. |
| Secondary Button | bg `#B5D2E6`, teks `#326080`, hover `#9CC2DA`. |
| Accent Button | bg `#805232`, teks putih, hover `#6A4229`. |
| Card | bg putih, border `#FFF1E7`, shadow lembut. |
| Section Background | `#FFF1E7` atau putih. |
| Info Alert | bg `#B5D2E6`, teks `#326080`. |
| Warning Alert | bg `#805232`, teks putih. |

---

## 3. Typography

- **Font:** Inter (fallback: `system-ui`, `sans-serif`).

| Style | Ukuran | Weight |
|---|---|---|
| H1 | 32px | Bold |
| H2 | 24px | Semibold |
| H3 | 20px | Semibold |
| Body | 16px | Regular |
| Small | 14px | Regular |
| Caption | 12px | Regular |

---

## 4. Spacing & Radius

- **Spacing scale:** 4, 8, 12, 16, 24, 32, 48, 64.
- **Radius:** `sm` = 4px, `md` = 8px, `lg` = 12px, `full` = 9999px.
- **Shadow:** `sm`, `md`, `lg` (gunakan default Tailwind).

---

## 5. Komponen

| Komponen | Ketentuan |
|---|---|
| Button | Varian: primary, secondary, accent, ghost, danger. |
| Input | Border `#B5D2E6`, focus ring `#326080`. |
| Card | bg putih, radius `lg`, shadow `sm`. |
| Badge | Status (DRAFT, PENDING, SIGNED, REJECTED) dengan warna berbeda. |
| Alert | Varian: info, success, warning, error. |
| Modal | Overlay hitam 50%, card putih. |
| Table | Header bg `#FFF1E7`, row hover `#FFF1E7`. |
| Sidebar | bg `#326080`, teks putih, active bg `#B5D2E6`. |

---

## 6. Layout

- **Landing Layout** — Header transparan, Hero full-width, section bergantian putih/cream.
- **Dashboard Layout** — Sidebar kiri (fixed), header atas (putih, shadow), konten bg `#FFF1E7`.

---

## 7. Design Token (Tailwind)

```js
// tailwind.config.js
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        white: '#FFFFFF',
        cream: '#FFF1E7',
        'light-blue': '#B5D2E6',
        'deep-blue': '#326080',
        brown: '#805232',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        sm: '4px',
        md: '8px',
        lg: '12px',
      },
    },
  },
  plugins: [],
}
```

---

## 8. Aksesibilitas

- Kontras teks minimal 4.5:1.
- Fokus state jelas (ring `#326080`).
- Alt text untuk gambar.
- ARIA label untuk ikon button.

---

## 10. Aturan untuk AI Agent

1. Baca `design.md` ini sebelum menulis kode UI apa pun (FE1 & FE2).
2. Jangan membuat warna baru di luar palet Section 2.
3. Jangan mengubah nilai spacing/radius/typography tanpa persetujuan pemilik design system (FE1).
4. Selalu pastikan kontras dan aksesibilitas sesuai Section 8 sebelum komponen dianggap selesai.
