<template>
  <div class="min-h-screen bg-[#FAFAF8] font-sans text-slate-900">
    <a href="#konten-dashboard" class="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:bg-white focus:p-2">
      Lewati ke konten
    </a>

    <!-- Tombol menu melayang (khusus layar kecil) -->
    <button
      type="button"
      class="fixed left-4 top-4 z-40 rounded-md bg-white p-2 text-deep-blue shadow-md lg:hidden"
      aria-label="Buka menu navigasi"
      :aria-expanded="sidebarOpen"
      @click="sidebarOpen = true"
    >
      <Menu class="h-5 w-5" aria-hidden="true" />
    </button>

    <!-- Sidebar -->
    <div v-if="sidebarOpen" class="fixed inset-0 z-20 bg-black/50 lg:hidden" aria-hidden="true" @click="sidebarOpen = false" />
    <aside
      class="fixed bottom-0 left-0 top-0 z-20 flex w-64 flex-col border-r border-slate-200 bg-white transition-transform lg:translate-x-0"
      :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full'"
      aria-label="Navigasi dashboard"
    >
      <div class="flex h-16 items-center gap-2 px-4">
        <span class="inline-flex h-8 w-8 items-center justify-center rounded-md bg-deep-blue text-white" aria-hidden="true">
          <FileText class="h-4 w-4" />
        </span>
        <span class="leading-tight">
          <span class="block text-[15px] font-bold text-slate-900">SecureSign</span>
          <span class="block text-[10px] font-medium tracking-wider text-slate-400">TANDA TANGAN DIGITAL</span>
        </span>
      </div>
      <nav class="flex-1 space-y-1 overflow-y-auto px-3 py-4">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-slate-500 hover:bg-slate-100 hover:text-slate-900 focus-visible:outline-2 focus-visible:outline-deep-blue"
          active-class="!bg-slate-100 !text-slate-900 !font-semibold"
          @click="sidebarOpen = false"
        >
          <component :is="item.icon" class="h-4 w-4" aria-hidden="true" />
          {{ item.label }}
          <span
            v-if="item.badge && item.badge > 0"
            class="ml-auto inline-flex min-h-5 min-w-5 items-center justify-center rounded-full bg-brown px-1.5 text-xs font-bold text-white"
            role="status"
            :aria-label="`${item.badge} dokumen menunggu`"
          >
            {{ item.badge }}
          </span>
        </RouterLink>
      </nav>

      <!-- Notifikasi -->
      <div class="px-3 pb-2">
        <button
          type="button"
          class="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-slate-500 hover:bg-slate-100 hover:text-slate-900"
          :aria-expanded="notifOpen"
          aria-label="Notifikasi"
          @click="notifOpen = !notifOpen"
        >
          <span class="relative">
            <Bell class="h-4 w-4" aria-hidden="true" />
            <span
              v-if="unreadCount > 0"
              class="absolute -right-2 -top-2 inline-flex min-h-4 min-w-4 items-center justify-center rounded-full bg-brown px-1 text-[10px] font-bold text-white"
              role="status"
              :aria-label="`${unreadCount} notifikasi belum dibaca`"
            >
              {{ unreadCount }}
            </span>
          </span>
          Notifikasi
          <ChevronDown class="ml-auto h-4 w-4 text-slate-400" aria-hidden="true" />
        </button>
        <div v-if="notifOpen" class="mt-1 max-h-64 overflow-auto rounded-md border border-slate-200 bg-white p-2 text-slate-900 shadow-sm" role="region" aria-label="Notifikasi">
          <div class="flex items-center justify-between px-2 py-1">
            <p class="text-sm font-semibold text-deep-blue">Notifikasi</p>
            <button type="button" class="text-xs text-deep-blue hover:underline" @click="markAllRead">Tandai dibaca</button>
          </div>
          <p v-if="notifications.length === 0" class="px-2 py-4 text-center text-sm text-slate-500">Tidak ada notifikasi.</p>
          <ul v-else>
            <li v-for="n in notifications" :key="n.id" class="rounded-md px-2 py-2 hover:bg-slate-50">
              <p class="text-sm font-semibold">{{ n.title }}</p>
              <p v-if="n.message" class="text-xs text-slate-600">{{ n.message }}</p>
            </li>
          </ul>
        </div>
      </div>

      <!-- Profil pengguna (bawah sidebar) -->
      <div class="relative border-t border-slate-100 p-3">
        <div
          v-if="userOpen"
          class="absolute inset-x-3 bottom-full mb-2 rounded-md border border-slate-200 bg-white py-1 text-slate-900 shadow-lg"
          role="menu"
        >
          <button type="button" role="menuitem" class="block w-full px-4 py-2 text-left text-sm hover:bg-slate-50" @click="goHome">
            Profil saya
          </button>
          <button type="button" role="menuitem" class="block w-full px-4 py-2 text-left text-sm text-[#B3261E] hover:bg-slate-50" @click="logout">
            Keluar
          </button>
        </div>
        <button
          type="button"
          class="flex w-full items-center gap-2 rounded-md p-1.5 text-left hover:bg-slate-100"
          aria-label="Menu pengguna"
          :aria-expanded="userOpen"
          @click="userOpen = !userOpen"
        >
          <span class="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-deep-blue text-sm font-bold text-white" aria-hidden="true">
            {{ initial }}
          </span>
          <span class="min-w-0 flex-1 text-left">
            <span class="block truncate text-sm font-semibold text-slate-900">{{ userName }}</span>
            <span class="block truncate text-xs text-slate-400">{{ userEmail }}</span>
          </span>
          <ChevronsUpDown class="h-4 w-4 shrink-0 text-slate-400" aria-hidden="true" />
        </button>
      </div>
    </aside>

    <!-- Konten -->
    <main id="konten-dashboard" class="mx-auto max-w-6xl px-4 pb-10 pt-16 lg:pl-72 lg:pt-8" tabindex="-1">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Bell, ChevronDown, ChevronsUpDown, Files, FileText, Home, Inbox, Layers, LayoutDashboard, Menu, ScrollText, ShieldCheck, Upload, Users } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/authStore'
import { useNotificationStore } from '@/stores/notificationStore'
import { useDocumentStore } from '@/stores/documentStore'

const router = useRouter()
const auth = useAuthStore()
const notifStore = useNotificationStore()
const docStore = useDocumentStore()

const sidebarOpen = ref(false)
const notifOpen = ref(false)
const userOpen = ref(false)

const userName = computed(() => auth.user?.fullName ?? 'Pengguna')
const userEmail = computed(() => auth.user?.email ?? (auth.user?.role ?? '-'))
const initial = computed(() => (userName.value.charAt(0) || 'P').toUpperCase())
const unreadCount = computed(() => notifStore.unreadCount + docStore.notifications.filter((n) => !n.isRead).length)
const notifications = computed(() => [
  ...notifStore.items.map((i) => ({ id: i.id, title: i.title, message: i.message ?? '' })),
  ...docStore.notifications.map((n) => ({ id: n.id, title: n.title, message: n.message })),
])

const navItems = computed(() => {
  const role = auth.user?.role
  const items: Array<{ to: string; label: string; icon: unknown; badge?: number }> = []
  if (role === 'SEKRETARIAT' || role === 'SUPER_ADMIN') {
    items.push({ to: '/org', label: 'Dashboard', icon: LayoutDashboard })
    items.push({ to: '/org/upload', label: 'Unggah Dokumen', icon: Upload })
    items.push({ to: '/org/documents', label: 'Dokumen', icon: Files })
  }
  if (role === 'SIGNER' || role === 'SUPER_ADMIN') {
    items.push({ to: '/signer', label: 'Permintaan Tanda Tangan', icon: Inbox, badge: docStore.pendingTotal })
    items.push({ to: '/signer/batch', label: 'Batch Signing', icon: Layers })
  }
  if (role === 'SUPER_ADMIN') {
    items.push({ to: '/admin', label: 'Ringkasan Platform', icon: Home })
    items.push({ to: '/admin/users', label: 'Manajemen User', icon: Users })
    items.push({ to: '/admin/audit', label: 'Audit Log', icon: ScrollText })
  }
  if (items.length === 0) items.push({ to: '/', label: 'Beranda', icon: Home })
  items.push({ to: '/verify', label: 'Verifikasi', icon: ShieldCheck })
  return items
})

function markAllRead() {
  notifStore.markAllRead()
  notifOpen.value = false
}

function goHome() {
  userOpen.value = false
  router.push(auth.roleHome())
}

async function logout() {
  userOpen.value = false
  await auth.logout()
  router.push('/login')
}
</script>
