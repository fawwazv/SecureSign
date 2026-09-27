<template>
  <div class="bg-cream/60">
    <div class="sv-container flex min-h-[calc(100vh-16rem)] items-center justify-center py-12">
      <Card class="w-full max-w-md text-center" title="403 — Akses ditolak">
        <p class="text-slate-600">Peran Anda tidak memiliki akses ke halaman ini.</p>
        <RouterLink to="/" class="mt-4 inline-block">
          <Button variant="secondary">Kembali ke beranda</Button>
        </RouterLink>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button, Card } from '@/components/ui'
</script>
