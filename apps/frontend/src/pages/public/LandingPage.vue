<template>
  <div>
    <!-- HERO -->
    <section class="bg-white">
      <div class="sv-container grid items-center gap-10 py-14 lg:grid-cols-2 lg:py-20">
        <div>
          <Badge tone="pending">MVP • RSA / ECDSA / Ed25519</Badge>
          <h1 class="mt-4 text-deep-blue">
            Tanda tangan PDF digital yang aman &amp; terverifikasi.
          </h1>
          <p class="mt-4 text-slate-600">
            SignVault menggantikan tanda tangan basah dengan kriptografi modern, alur
            persetujuan multi-pihak, QR verifikasi, dan audit trail — tanpa blockchain.
          </p>
          <div class="mt-6 flex flex-wrap gap-3">
            <RouterLink to="/register"><Button size="lg">Mulai Gratis</Button></RouterLink>
            <RouterLink to="/verify"><Button variant="secondary" size="lg">Verifikasi Dokumen</Button></RouterLink>
          </div>
          <dl class="mt-8 grid grid-cols-3 gap-4 text-center">
            <div class="sv-card p-4">
              <dt class="text-xs text-slate-500">Penandatanganan</dt>
              <dd class="text-xl font-bold text-deep-blue">&lt; 3 dtk</dd>
            </div>
            <div class="sv-card p-4">
              <dt class="text-xs text-slate-500">Verifikasi</dt>
              <dd class="text-xl font-bold text-deep-blue">&lt; 2 dtk</dd>
            </div>
            <div class="sv-card p-4">
              <dt class="text-xs text-slate-500">Uptime MVP</dt>
              <dd class="text-xl font-bold text-deep-blue">99,5%</dd>
            </div>
          </dl>
        </div>
        <div class="sv-card p-6" aria-label="Ilustrasi alur tanda tangan">
          <div class="flex items-center justify-between">
            <p class="font-semibold text-deep-blue">Kontrak_Kerja.pdf</p>
            <Badge tone="signed">SIGNED</Badge>
          </div>
          <div class="mt-4 rounded-md bg-cream p-4 text-sm text-slate-600">
            <p class="font-mono text-xs">SHA-256: 9f2c…a41d ✓ cocok</p>
            <p class="font-mono text-xs">ECDSA P-256 • signature valid</p>
            <p class="font-mono text-xs">QR tertempel • halaman terakhir</p>
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
          Semua yang dibutuhkan untuk mengganti tanda tangan basah — dari upload hingga audit.
        </p>
        <div class="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
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
          <Card title="HR & Legal" subtitle="Kontrak kerja, NDA, PKWT — batch signing puluhan dokumen sekaligus.">
            <Badge tone="neutral">Org Admin + Signer</Badge>
          </Card>
          <Card title="Keuangan" subtitle="Persetujuan invoice & pengajuan dana multi-direktur dengan audit trail.">
            <Badge tone="info">Multi-Signer</Badge>
          </Card>
          <Card title="Mitra / Publik" subtitle="Verifikasi keaslian dokumen via QR tanpa perlu akun.">
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
import { FileCheck2, BellRing, QrCode, ScrollText, ShieldCheck, Users, Zap } from 'lucide-vue-next'
import { Badge, Button, Card, Table } from '@/components/ui'

const features = [
  { title: 'Upload PDF', desc: 'Org Admin upload hingga 25 MB ke Supabase Storage.', icon: FileCheck2 },
  { title: 'Multi-Signer', desc: 'Minta tanda tangan ke banyak pihak + notifikasi email & in-app.', icon: Users },
  { title: 'Batch Signing', desc: 'Signer setujui puluhan dokumen dalam sekali aksi.', icon: Zap },
  { title: 'QR Verifikasi', desc: 'QR tertempel berisi hash + tautan verifikasi publik.', icon: QrCode },
  { title: 'Verifikasi Publik', desc: 'Scan QR / upload PDF — hasil VALID / TIDAK VALID.', icon: ScrollText },
  { title: 'Audit Log', desc: 'Immutable log untuk setiap aksi sign & verify.', icon: BellRing },
  { title: 'Manajemen Kunci', desc: 'RSA-2048 PSS, ECDSA P-256, Ed25519. Revoke oleh Super Admin.', icon: ShieldCheck },
  { title: 'Notifikasi', desc: 'Email + in-app untuk request, signed, dan rejected.', icon: BellRing },
]

const steps = [
  { title: 'Upload', desc: 'Org Admin upload PDF + isi metadata dokumen.' },
  { title: 'Request', desc: 'Pilih signer, sistem kirim notifikasi.' },
  { title: 'Review & Sign', desc: 'Signer preview, setujui/tolak, kunci privat dibuka via AES-256-GCM.' },
  { title: 'QR + Verifikasi', desc: 'QR tertempel, siapa pun bisa verifikasi tanpa login.' },
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
  { q: 'Apakah perlu login untuk verifikasi?', a: 'Tidak. Halaman /verify terbuka untuk publik — cukup upload PDF atau pindai QR.' },
  { q: 'Format dokumen apa yang didukung?', a: 'MVP mendukung PDF hingga 25 MB.' },
  { q: 'Apakah sah secara hukum?', a: 'MVP ini prototipe teknis. Untuk kekuatan hukum penuh perlu integrasi PSrE/TTE, e-KYC, dan e-Meterai.' },
  { q: 'Bagaimana jika QR dipalsukan?', a: 'Verifikasi selalu server-side: hash + signature dicek ulang, QR palsu akan berstatus TIDAK VALID.' },
]
</script>
