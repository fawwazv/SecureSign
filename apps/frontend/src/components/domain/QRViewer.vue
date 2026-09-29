<template>
  <Card title="QR Verifikasi" subtitle="Pindai untuk verifikasi publik tanpa login">
    <div class="flex flex-col items-center gap-3">
      <div v-if="info" class="w-full rounded-md bg-cream p-3 text-sm">
        <p class="font-semibold text-deep-blue">{{ info.name || 'Dokumen bertanda' }}</p>
        <dl class="mt-1 grid grid-cols-2 gap-x-3 gap-y-1 text-xs text-slate-600">
          <div v-if="info.position"><dt class="inline font-medium">Jabatan: </dt><dd class="inline">{{ info.position }}</dd></div>
          <div v-if="info.org"><dt class="inline font-medium">Institusi: </dt><dd class="inline">{{ info.org }}</dd></div>
          <div v-if="info.signedAt"><dt class="inline font-medium">Tanggal: </dt><dd class="inline">{{ info.signedAt }}</dd></div>
          <div v-if="info.algorithm"><dt class="inline font-medium">Algoritma: </dt><dd class="inline">{{ info.algorithm }}</dd></div>
        </dl>
        <p class="mt-2 text-[11px] italic text-slate-500">
          Info dari QR (rujukan, belum terverifikasi) — keaslian dipastikan lewat pemeriksaan kriptografis.
        </p>
      </div>
      <div v-else class="flex w-full items-center gap-2 rounded-md bg-cream p-3">
        <QrCode class="h-5 w-5 shrink-0 text-brown" aria-hidden="true" />
        <p class="min-w-0 flex-1 break-all text-sm text-deep-blue">{{ displayUrl }}</p>
      </div>
      <div class="flex flex-wrap justify-center gap-2">
        <Button variant="secondary" size="sm" @click="copy">
          <Copy class="h-4 w-4" aria-hidden="true" /> {{ copied ? 'Tersalin!' : 'Salin tautan' }}
        </Button>
        <Button variant="ghost" size="sm" @click="open">
          <ExternalLink class="h-4 w-4" aria-hidden="true" /> Buka verifikasi
        </Button>
      </div>
      <p class="text-xs text-slate-500">Gambar QR digambar di dokumen final oleh backend (pyhanko + qrcode).</p>
    </div>
  </Card>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Copy, ExternalLink, QrCode } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import { extractVerifyUrl, parseQrPayload } from '@/utils/qr'

const props = defineProps<{ qrPayload: string }>()
const copied = ref(false)

const info = computed(() => parseQrPayload(props.qrPayload))
const displayUrl = computed(() => extractVerifyUrl(props.qrPayload))

async function copy() {
  try {
    await navigator.clipboard.writeText(displayUrl.value)
    copied.value = true
    setTimeout(() => (copied.value = false), 2000)
  } catch {
    copied.value = false
  }
}

function open() {
  window.open(displayUrl.value, '_blank', 'noopener')
}
</script>
