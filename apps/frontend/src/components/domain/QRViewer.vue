<template>
  <Card title="QR Verifikasi" subtitle="Pindai untuk verifikasi publik tanpa login">
    <div class="flex flex-col items-center gap-3">
      <div class="flex w-full items-center gap-2 rounded-md bg-cream p-3">
        <QrCode class="h-5 w-5 shrink-0 text-brown" aria-hidden="true" />
        <p class="min-w-0 flex-1 break-all text-sm text-deep-blue">{{ qrPayload }}</p>
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
import { ref } from 'vue'
import { Copy, ExternalLink, QrCode } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'

const props = defineProps<{ qrPayload: string }>()
const copied = ref(false)

async function copy() {
  try {
    await navigator.clipboard.writeText(props.qrPayload)
    copied.value = true
    setTimeout(() => (copied.value = false), 2000)
  } catch {
    copied.value = false
  }
}

function open() {
  window.open(props.qrPayload, '_blank', 'noopener')
}
</script>
