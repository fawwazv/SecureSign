<template>
  <div class="flex min-h-screen flex-col bg-white">
    <a href="#main" class="sr-only focus:not-sr-only focus:absolute focus:p-2 focus:bg-light-blue">
      Lewati ke konten utama
    </a>

    <!-- Header publik -->
    <header class="sticky top-0 z-40 border-b border-cream bg-white/90 backdrop-blur">
      <div class="sv-container flex h-16 items-center justify-between gap-4">
        <RouterLink to="/" class="flex items-center gap-2" aria-label="SignVault beranda">
          <span class="flex h-9 w-9 items-center justify-center rounded-md bg-deep-blue text-white">
            <ShieldCheck class="h-5 w-5" aria-hidden="true" />
          </span>
          <span class="text-lg font-bold text-deep-blue">SignVault</span>
        </RouterLink>

        <nav class="hidden items-center gap-6 text-sm font-medium text-slate-700 md:flex" aria-label="Navigasi utama">
          <RouterLink to="/#fitur" class="hover:text-deep-blue">Fitur</RouterLink>
          <RouterLink to="/#cara-kerja" class="hover:text-deep-blue">Cara Kerja</RouterLink>
          <RouterLink to="/#keamanan" class="hover:text-deep-blue">Keamanan</RouterLink>
          <RouterLink to="/#faq" class="hover:text-deep-blue">FAQ</RouterLink>
          <RouterLink to="/verify" class="hover:text-deep-blue">Verifikasi</RouterLink>
        </nav>

        <div class="flex items-center gap-2">
          <RouterLink to="/login">
            <Button variant="ghost" size="sm">Masuk</Button>
          </RouterLink>
          <RouterLink to="/register">
            <Button variant="primary" size="sm">Daftar Gratis</Button>
          </RouterLink>
        </div>
      </div>
    </header>

    <!-- Konten -->
    <main id="main" class="flex-1">
      <RouterView />
    </main>

    <!-- Footer publik -->
    <footer class="border-t border-cream bg-deep-blue text-white">
      <div class="sv-container grid gap-8 py-12 md:grid-cols-4">
        <div>
          <div class="flex items-center gap-2">
            <span class="flex h-9 w-9 items-center justify-center rounded-md bg-white text-deep-blue">
              <ShieldCheck class="h-5 w-5" aria-hidden="true" />
            </span>
            <span class="text-lg font-bold">SignVault</span>
          </div>
          <p class="mt-3 text-sm text-white/80">
            Tanda tangan dokumen elektronik yang aman, cepat, dan terverifikasi.
          </p>
        </div>
        <nav aria-label="Produk">
          <p class="font-semibold">Produk</p>
          <ul class="mt-3 space-y-2 text-sm text-white/80">
            <li><RouterLink to="/#fitur" class="hover:text-white">Fitur</RouterLink></li>
            <li><RouterLink to="/#cara-kerja" class="hover:text-white">Cara Kerja</RouterLink></li>
            <li><RouterLink to="/verify" class="hover:text-white">Verifikasi Publik</RouterLink></li>
          </ul>
        </nav>
        <nav aria-label="Akun">
          <p class="font-semibold">Akun</p>
          <ul class="mt-3 space-y-2 text-sm text-white/80">
            <li><RouterLink to="/login" class="hover:text-white">Masuk</RouterLink></li>
            <li><RouterLink to="/register" class="hover:text-white">Daftar</RouterLink></li>
            <li><RouterLink to="/forgot-password" class="hover:text-white">Lupa Kata Sandi</RouterLink></li>
          </ul>
        </nav>
        <div>
          <p class="font-semibold">Keamanan</p>
          <ul class="mt-3 space-y-2 text-sm text-white/80">
            <li>RSA-2048 PSS / ECDSA P-256 / Ed25519</li>
            <li>AES-256-GCM untuk private key</li>
            <li>Audit trail immutable</li>
          </ul>
        </div>
      </div>
      <div class="border-t border-white/20">
        <div class="sv-container flex flex-col items-center justify-between gap-2 py-4 text-xs text-white/70 sm:flex-row">
          <p>© 2026 SignVault. Prototipe MVP — bukan PSrE tersertifikasi.</p>
          <p>UU ITE • PDP • OWASP Top 10</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ShieldCheck } from 'lucide-vue-next'
import { Button } from '@/components/ui'
</script>
