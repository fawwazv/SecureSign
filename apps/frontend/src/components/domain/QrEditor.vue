<template>
  <div class="flex flex-col gap-3">
    <div class="flex flex-wrap items-center gap-2">
      <Button variant="secondary" size="sm" :disabled="!canEdit" @click="addBox">
        + Tambah QR Code
      </Button>
      <div v-if="pageCount > 1" class="flex items-center gap-2 text-sm">
        <label :for="`qr-page-${documentId}`" class="text-slate-600">Halaman</label>
        <select
          :id="`qr-page-${documentId}`" v-model.number="page" :disabled="!canEdit"
          class="rounded-md border border-light-blue bg-white px-2 py-1"
        >
          <option v-for="p in pageCount" :key="p" :value="p">Halaman {{ p }}</option>
        </select>
      </div>
      <span class="text-xs text-slate-500">Total QR: {{ boxes.length }}</span>
    </div>

    <div ref="stageRef" class="relative touch-none overflow-hidden rounded-md border border-dashed border-light-blue bg-slate-50" style="min-height: 120px">
      <slot />
      <div
        v-for="b in boxesOnPage" :key="b.id"
        class="absolute border-2 border-deep-blue bg-deep-blue/10"
        :style="{ left: `${b.x * 100}%`, top: `${b.y * 100}%`, width: `${b.size * 100}%`, aspectRatio: '1 / 1' }"
        @pointerdown="startDrag($event, b, 'move')"
      >
        <span class="absolute left-1 top-1 rounded bg-deep-blue px-1 text-[10px] font-bold text-white">QR</span>
        <span
          class="absolute -bottom-2 -right-2 h-5 w-5 cursor-nwse-resize rounded-full border-2 border-white bg-deep-blue"
          @pointerdown.stop="startDrag($event, b, 'resize')"
        />
        <button
          class="absolute -right-2 -top-2 flex h-5 w-5 items-center justify-center rounded-full bg-[#B3261E] text-[10px] font-bold text-white"
          aria-label="Hapus QR" @click.stop="removeBox(b.id)"
        >
          ✕
        </button>
      </div>
      <p v-if="!boxesOnPage.length" class="pointer-events-none absolute inset-0 flex items-center justify-center p-6 text-center text-xs text-slate-400">
        Klik “Tambah QR Code”, lalu geser dan ubah ukurannya ke posisi yang sesuai.
      </p>
    </div>

    <Button variant="primary" :disabled="!canEdit || !dirty" :loading="saving" @click="save">
      Saya sudah yakin dengan posisi QR code
    </Button>
    <p v-if="savedTick" class="text-xs text-[#1B7A3D]">Posisi tersimpan.</p>
    <p v-if="saveError" role="alert" class="text-xs text-[#B3261E]">{{ saveError }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import Button from '@/components/ui/Button.vue'
import { saveQrPlacements } from '@/services/documentService'
import { toApiMessage } from '@/services/apiClient'

export interface QrBox {
  id: number
  page: number
  x: number
  y: number
  size: number
}

const props = defineProps<{
  documentId: string
  pageCount: number
  initial: { page: number; x: number; y: number; size: number }[]
  canEdit: boolean
}>()

const emit = defineEmits<{ saved: [placements: { page: number; x: number; y: number; size: number }[]] }>()

const stageRef = ref<HTMLElement | null>(null)
const page = ref(1)
const boxes = ref<QrBox[]>(props.initial.map((p, i) => ({ ...p, id: i + 1 })))
let seq = props.initial.length
const saving = ref(false)
const saveError = ref('')
const savedTick = ref(false)
const dirty = ref(false)

const boxesOnPage = computed(() => boxes.value.filter((b) => b.page === page.value))

let seqCounter = seq
function addBox() {
  seqCounter += 1
  boxes.value.push({ id: seqCounter, page: page.value, x: 0.65, y: 0.75, size: 0.15 })
  dirty.value = true
  savedTick.value = false
}

function removeBox(id: number) {
  boxes.value = boxes.value.filter((b) => b.id !== id)
  dirty.value = true
  savedTick.value = false
}

interface DragState {
  id: number
  mode: 'move' | 'resize'
  startX: number
  startY: number
  orig: QrBox
}

let drag: DragState | null = null

function clamp(v: number, lo: number, hi: number) {
  return Math.min(hi, Math.max(lo, v))
}

function startDrag(e: PointerEvent, box: QrBox, mode: 'move' | 'resize') {
  if (!props.canEdit) return
  const el = stageRef.value
  if (!el) return
  ;(e.target as HTMLElement).setPointerCapture?.(e.pointerId)
  drag = { id: box.id, mode, startX: e.clientX, startY: e.clientY, orig: { ...box } }
  const move = (ev: PointerEvent) => {
    if (!drag || !el) return
    const rect = el.getBoundingClientRect()
    const dx = (ev.clientX - drag.startX) / rect.width
    const dy = (ev.clientY - drag.startY) / rect.height
    const b = boxes.value.find((x) => x.id === drag!.id)
    if (!b) return
    if (drag.mode === 'move') {
      b.x = clamp(drag.orig.x + dx, 0, 1 - b.size)
      b.y = clamp(drag.orig.y + dy, 0, 1 - b.size)
    } else {
      b.size = clamp(drag.orig.size + Math.max(dx, dy), 0.02, 0.8)
      b.x = clamp(b.x, 0, 1 - b.size)
      b.y = clamp(b.y, 0, 1 - b.size)
    }
    dirty.value = true
    savedTick.value = false
  }
  const up = () => {
    window.removeEventListener('pointermove', move)
    window.removeEventListener('pointerup', up)
    drag = null
  }
  window.addEventListener('pointermove', move)
  window.addEventListener('pointerup', up)
  e.preventDefault()
}

async function save() {
  saveError.value = ''
  savedTick.value = false
  saving.value = true
  try {
    const placements = boxes.value.map(({ page: p, x, y, size }) => ({ page: p, x, y, size }))
    await saveQrPlacements(props.documentId, placements)
    dirty.value = false
    savedTick.value = true
    emit('saved', placements)
  } catch (e) {
    saveError.value = toApiMessage(e, 'Penyimpanan posisi gagal.')
  } finally {
    saving.value = false
  }
}
</script>
