<template>
  <div>
    <!-- HERO -->
    <section class="bg-white">
      <div class="sv-container grid items-center gap-10 py-14 lg:grid-cols-2 lg:py-20">
        <div>
          <Badge tone="pending">MVP • RSA / ECDSA / Ed25519</Badge>
          <h1 class="mt-4 text-deep-blue">
            Tanda tangan surat akademik yang aman &amp; terverifikasi.
          </h1>
          <p class="mt-4 text-slate-600">
            SignVault menggantikan tanda tangan basah untuk surat kampus — alur
            Sekretariat ke Signer, metadata Nama &amp; NIM ikut ditandatangani,
            QR verifikasi presisi, dan audit trail.
          </p>
          <div class="mt-6 flex flex-wrap gap-3">
            <RouterLink to="/register"><Button size="lg">Mulai Gratis</Button></RouterLink>
            <RouterLink to="/verify"><Button variant="secondary" size="lg">Verifikasi Dokumen</Button></RouterLink>
          </div>
          <dl class="mt-8 grid grid-cols-3 gap-4 text-center">
            <div class="sv-card p-4">
              <dt class="text-xs text-slate-500">Penandatanganan</dt>
              <dd class="text-xl font-bold text-deep-blue">≈ 0,2 ms</dd>
            </div>
            <div class="sv-card p-4">
              <dt class="text-xs text-slate-500">Verifikasi</dt>
              <dd class="text-xl font-bold text-deep-blue">≈ 0,1 ms</dd>
            </div>
            <div class="sv-card p-4">
              <dt class="text-xs text-slate-500">Iterasi teruji</dt>
              <dd class="text-xl font-bold text-deep-blue">30×</dd>
            </div>
          </dl>
        </div>
        <div class="sv-card p-6" aria-label="Ilustrasi alur tanda tangan">
          <div class="flex items-center justify-between">
            <p class="font-semibold text-deep-blue">SK-Aktif-Kuliah.pdf</p>
            <Badge tone="signed">SIGNED</Badge>
          </div>
          <div class="mt-4 rounded-md bg-cream p-4 text-sm text-slate-600">
            <p class="font-mono text-xs">SHA-256: 9f2c…a41d ✓ cocok</p>
            <p class="font-mono text-xs">Ed25519 • signature valid</p>
            <p class="font-mono text-xs">QR tertempel • posisi presisi</p>
          </div>
          <div class="mt-4 flex items-center gap-3">
            <div class="flex h-16 w-16 items-center justify-center rounded-md bg-deep-blue text-white">
              <QrCode class="h-8 w-8" aria-hidden="true" />
            </div>
            <div class="text-sm">
              <p class="font-semibold">Pindai untuk verifikasi publik</p>
              <p class="text-slate-500">Tanpa login • hasil VALID / TIDAK VALID</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- FITUR -->
    <section id="fitur" class="bg-cream">
      <div class="sv-container sv-section">
        <h2 class="text-center text-deep-blue">Fitur utama MVP</h2>
        <p class="mx-auto mt-2 max-w-2xl text-center text-slate-600">
          Semua yang dibutuhkan administrasi kampus — dari upload surat hingga audit.
        </p>
        <div class="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Card v-for="f in features" :key="f.title" :title="f.title" :subtitle="f.desc">
            <component :is="f.icon" class="h-6 w-6 text-brown" aria-hidden="true" />
          </Card>
        </div>
      </div>
    </section>

    <!-- CARA KERJA -->
    <section id="cara-kerja" class="bg-white">
      <div class="sv-container sv-section">
        <h2 class="text-center text-deep-blue">Cara kerja</h2>
        <ol class="mt-8 grid gap-4 md:grid-cols-4">
          <li v-for="(s, i) in steps" :key="s.title" class="sv-card p-5">
            <p class="flex h-8 w-8 items-center justify-center rounded-full bg-deep-blue text-sm font-bold text-white">{{ i + 1 }}</p>
            <p class="mt-3 font-semibold">{{ s.title }}</p>
            <p class="mt-1 text-sm text-slate-600">{{ s.desc }}</p>
          </li>
        </ol>
      </div>
    </section>

    <!-- USE CASE -->
    <section class="bg-cream">
      <div class="sv-container sv-section">
        <h2 class="text-center text-deep-blue">Cocok untuk</h2>
        <div class="mt-8 grid gap-4 md:grid-cols-3">
          <Card title="Kemahasiswaan & Akademik" subtitle="SK aktif/lulus, surat TA, rekomendasi beasiswa, KP/magang — lengkap dengan Nama & NIM.">
            <Badge tone="neutral">Sekretariat + Signer</Badge>
          </Card>
          <Card title="Fakultas & Prodi" subtitle="Penandatangan Kaprodi/Dekan dengan jabatan tercatat + audit trail.">
            <Badge tone="info">Signer</Badge>
          </Card>
          <Card title="Pemberi Beasiswa / Publik" subtitle="Verifikasi keaslian surat via QR tanpa perlu akun.">
            <Badge tone="pending">Verifier</Badge>
          </Card>
        </div>
      </div>
    </section>

    <!-- KEAMANAN -->
    <section id="keamanan" class="bg-white">
      <div class="sv-container sv-section grid gap-8 lg:grid-cols-2">
        <div>
          <h2 class="text-deep-blue">Keamanan setara enterprise</h2>
          <ul class="mt-4 space-y-3 text-slate-700">
            <li v-for="k in security" :key="k" class="flex gap-2">
              <ShieldCheck class="h-5 w-5 shrink-0 text-deep-blue" aria-hidden="true" />
              <span>{{ k }}</span>
            </li>
          </ul>
          <p class="mt-4 text-sm text-slate-500">
            Private key tidak pernah keluar server; sesi per-tab dengan refresh toleran balapan antar-tab.
          </p>
        </div>
        <Card title="Stack kriptografi" subtitle="Implementasi Python `cryptography` di backend.">
          <Table :columns="cryptoCols" :rows="cryptoRows" />
        </Card>
      </div>
    </section>

    <!-- FAQ -->
    <section id="faq" class="bg-cream">
      <div class="sv-container sv-section max-w-3xl">
        <h2 class="text-center text-deep-blue">Pertanyaan umum</h2>
        <div class="mt-6 space-y-3">
          <details v-for="f in faqs" :key="f.q" class="sv-card p-4">
            <summary class="cursor-pointer font-semibold text-deep-blue">{{ f.q }}</summary>
            <p class="mt-2 text-sm text-slate-600">{{ f.a }}</p>
          </details>
        </div>
        <div class="mt-8 text-center">
          <RouterLink to="/register"><Button variant="accent" size="lg">Daftar — gratis untuk MVP</Button></RouterLink>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { FileCheck2, BellRing, QrCode, ScrollText, ShieldCheck, Zap } from 'lucide-vue-next'
import { Badge, Button, Card, Table } from '@/components/ui'

const features = [
  { title: 'Upload PDF', desc: 'Sekretariat upload hingga 25 MB + metadata Nama, NIM, dan 11 jenis surat akademik.', icon: FileCheck2 },
  { title: 'QR Presisi', desc: 'Geser dan ubah ukuran QR mengikuti aspek halaman PDF yang sebenarnya.', icon: QrCode },
  { title: 'Batch Signing', desc: 'Signer setujui puluhan dokumen dalam sekali aksi.', icon: Zap },
  { title: 'QR Verifikasi', desc: 'QR berisi metadata + tautan verifikasi publik + caption ID.', icon: QrCode },
  { title: 'Verifikasi Publik', desc: 'Upload PDF, token/QR, file + kunci, atau scan kamera — VALID / TIDAK VALID.', icon: ScrollText },
  { title: 'Uji Performa 30×', desc: 'Ukur rata-rata Sign dan Verifikasi langsung dari halaman verifikasi.', icon: Zap },
  { title: 'Audit Log', desc: 'Jejak aksi sign & verify per aktor dan waktu.', icon: BellRing },
  { title: 'Manajemen Kunci', desc: 'RSA-2048 PSS, ECDSA P-256, Ed25519 terenkripsi AES-GCM. Revoke oleh Super Admin.', icon: ShieldCheck },
  { title: 'Notifikasi', desc: 'In-app untuk request, signed, dan rejected.', icon: BellRing },
]

const steps = [
  { title: 'Upload', desc: 'Sekretariat upload PDF + isi Nama, NIM, dan jenis surat.' },
  { title: 'Request', desc: 'Atur posisi QR lalu pilih signer (mis. Kaprodi).' },
  { title: 'Review & Sign', desc: 'Signer cek data dokumen, pilih key, isi jabatan.' },
  { title: 'QR + Verifikasi', desc: 'QR tertempel presisi; hasil tampil dengan jabatan & institusi.' },
]

const security = [
  'Hash SHA-256 atas byte PDF + canonicalization JCS/RFC 8785.',
  'Private key terenkripsi AES-256-GCM, KEK dari env / Supabase Vault.',
  'JWT access 15 menit + refresh 7 hari dengan rotasi.',
  'Password Argon2id, TLS 1.3, rate limit 60 req/menit, CORS ketat.',
]

const cryptoCols = [
  { key: 'alg', label: 'Algoritma' },
  { key: 'detail', label: 'Detail' },
]
const cryptoRows = [
  { alg: 'RSA-2048', detail: 'PSS salt 32, SHA-256' },
  { alg: 'ECDSA', detail: 'P-256, SHA-256 (default hemat)' },
  { alg: 'Ed25519', detail: 'Tanda tangan cepat & ringkas' },
]

const faqs = [
  { q: 'Apakah perlu login untuk verifikasi?', a: 'Tidak. Halaman /verify terbuka untuk publik — cukup upload PDF, tempel token/QR, file + kunci, atau pindai kamera.' },
  { q: 'Surat apa saja yang didukung?', a: '11 jenis surat akademik (SK aktif/lulus, TA, KP/magang, rekomendasi beasiswa, dan lainnya) plus Lainnya. PDF hingga 25 MB.' },
  { q: 'Bagaimana menguji kunci yang salah?', a: 'Lewat tab File + Kunci: unggah PDF bertanda yang sama lalu tempel kunci publik lain — hasilnya TIDAK VALID.' },
  { q: 'Format dokumen apa yang didukung?', a: 'MVP mendukung PDF hingga 25 MB.' },
  { q: 'Apakah sah secara hukum?', a: 'MVP ini prototipe teknis. Untuk kekuatan hukum penuh perlu integrasi PSrE/TTE, e-KYC, dan e-Meterai.' },
  { q: 'Bagaimana jika QR dipalsukan?', a: 'Verifikasi selalu server-side: hash + signature dicek ulang, QR palsu akan berstatus TIDAK VALID.' },
]
</script>
