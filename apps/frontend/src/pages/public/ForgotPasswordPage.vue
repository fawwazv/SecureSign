<template>
  <div class="bg-cream/60">
    <div class="sv-container flex min-h-[calc(100vh-16rem)] items-center justify-center py-12">
      <Card class="w-full max-w-md" title="Lupa kata sandi" subtitle="Reset kata sandi akun Anda.">
        <div class="space-y-4">
          <Alert variant="warning" title="Belum tersedia">
            Endpoint reset kata sandi belum disediakan backend MVP. Hubungi admin organisasi
            Anda untuk bantuan akun, atau daftar dengan email lain.
          </Alert>
          <Input
            id="email" v-model="email" label="Email" type="email" autocomplete="email"
            placeholder="nama@perusahaan.id" disabled
          />
          <Button type="button" block disabled>
            Kirim tautan reset
          </Button>
          <p class="text-center text-sm">
            <RouterLink to="/login" class="text-deep-blue hover:underline">Kembali masuk</RouterLink>
          </p>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Alert, Button, Card, Input } from '@/components/ui'

const email = ref('')
</script>
