<template>
  <div class="min-h-screen bg-cream font-sans text-slate-900">
    <a href="#konten-dashboard" class="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:bg-white focus:p-2">
      Lewati ke konten
    </a>
    <!-- Header atas -->
    <header class="fixed inset-x-0 top-0 z-30 flex h-16 items-center gap-3 bg-white px-4 shadow-sm lg:pl-72">
      <button
        type="button"
        class="rounded-md p-2 text-deep-blue hover:bg-cream lg:hidden"
        aria-label="Buka menu navigasi"
        :aria-expanded="sidebarOpen"
        @click="sidebarOpen = !sidebarOpen"
      >
        <Menu class="h-5 w-5" aria-hidden="true" />
      </button>
      <div class="min-w-0 flex-1">
        <p class="truncate text-sm text-slate-500">SignVault</p>
        <h1 class="truncate text-lg font-semibold text-deep-blue">{{ pageTitle }}</h1>
      </div>
      <button
        type="button"
        class="relative rounded-md p-2 text-deep-blue hover:bg-cream"
        aria-label="Notifikasi"
        @click="notifOpen = !notifOpen"
      >
        <Bell class="h-5 w-5" aria-hidden="true" />
        <span
          v-if="unreadCount > 0"
          class="absolute -right-0.5 -top-0.5 inline-flex min-h-5 min-w-5 items-center justify-center rounded-full bg-brown px-1 text-xs font-bold text-white"
          role="status"
          :aria-label="`${unreadCount} notifikasi belum dibaca`"
        >
          {{ unreadCount }}
        </span>
      </button>
      <div class="relative">
        <button
          type="button"
          class="flex items-center gap-2 rounded-md p-1.5 hover:bg-cream"
          aria-label="Menu pengguna"
          :aria-expanded="userOpen"
          @click="userOpen = !userOpen"
        >
          <span class="inline-flex h-8 w-8 items-center justify-center rounded-full bg-deep-blue text-sm font-bold text-white" aria-hidden="true">
            {{ initial }}
          </span>
          <span class="hidden text-left sm:block">
            <span class="block max-w-32 truncate text-sm font-semibold">{{ userName }}</span>
            <span class="block text-xs text-slate-500">{{ userRole }}</span>
          </span>
          <ChevronDown class="h-4 w-4 text-slate-500" aria-hidden="true" />
        </button>
        <div v-if="userOpen" class="absolute right-0 mt-2 w-48 rounded-md bg-white py-1 shadow-lg" role="menu">
          <button type="button" role="menuitem" class="block w-full px-4 py-2 text-left text-sm hover:bg-cream" @click="goHome">
            Profil saya
          </button>
          <button type="button" role="menuitem" class="block w-full px-4 py-2 text-left text-sm text-[#B3261E] hover:bg-cream" @click="logout">
            Keluar
          </button>
        </div>
      </div>
    </header>

    <!-- Dropdown notifikasi -->
    <div v-if="notifOpen" class="fixed right-4 top-16 z-30 w-80 max-w-[calc(100vw-2rem)] rounded-lg bg-white p-2 shadow-lg" role="region" aria-label="Notifikasi">
      <div class="flex items-center justify-between px-2 py-1">
        <p class="text-sm font-semibold text-deep-blue">Notifikasi</p>
        <button type="button" class="text-xs text-deep-blue hover:underline" @click="markAllRead">Tandai dibaca</button>
      </div>
      <p v-if="notifications.length === 0" class="px-2 py-4 text-center text-sm text-slate-500">Tidak ada notifikasi.</p>
      <ul v-else class="max-h-80 overflow-auto">
        <li v-for="n in notifications" :key="n.id" class="rounded-md px-2 py-2 hover:bg-cream">
          <p class="text-sm font-semibold">{{ n.title }}</p>
          <p v-if="n.message" class="text-xs text-slate-600">{{ n.message }}</p>
        </li>
      </ul>
    </div>

    <!-- Sidebar -->
    <div v-if="sidebarOpen" class="fixed inset-0 z-20 bg-black/50 lg:hidden" aria-hidden="true" @click="sidebarOpen = false" />
    <aside
      class="fixed bottom-0 left-0 top-0 z-20 w-64 bg-deep-blue text-white transition-transform lg:translate-x-0"
      :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full'"
      aria-label="Navigasi dashboard"
    >
      <div class="flex h-16 items-center gap-2 px-4">
        <span class="inline-flex h-8 w-8 items-center justify-center rounded-md bg-white font-bold text-deep-blue" aria-hidden="true">S</span>
        <span class="text-lg font-bold">SignVault</span>
      </div>
      <nav class="space-y-1 px-3 py-4">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium hover:bg-white/10 focus-visible:outline-2 focus-visible:outline-white"
          active-class="bg-light-blue !text-deep-blue"
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
      <div class="absolute bottom-0 w-full p-3 text-xs text-white/70">
        <p>{{ userRole }} · {{ userName }}</p>
      </div>
    </aside>

    <!-- Konten -->
    <main id="konten-dashboard" class="px-4 pb-10 pt-20 lg:pl-72" tabindex="-1">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Bell, ChevronDown, FileText, Home, Inbox, Layers, Menu, ScrollText, Upload, Users } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/authStore'
import { useNotificationStore } from '@/stores/notificationStore'
import { useDocumentStore } from '@/stores/documentStore'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const notifStore = useNotificationStore()
const docStore = useDocumentStore()

const sidebarOpen = ref(false)
const notifOpen = ref(false)
const userOpen = ref(false)

const userName = computed(() => auth.user?.fullName ?? 'Pengguna')
const userRole = computed(() => auth.user?.role ?? '-')
const initial = computed(() => (userName.value.charAt(0) || 'P').toUpperCase())
const unreadCount = computed(() => notifStore.unreadCount + docStore.notifications.filter((n) => !n.isRead).length)
const notifications = computed(() => [
  ...notifStore.items.map((i) => ({ id: i.id, title: i.title, message: i.message ?? '' })),
  ...docStore.notifications.map((n) => ({ id: n.id, title: n.title, message: n.message })),
])
const pageTitle = computed(() => (route.meta.title as string) || 'Dashboard')

const navItems = computed(() => {
  const role = auth.user?.role
  const items: Array<{ to: string; label: string; icon: unknown; badge?: number }> = []
  if (role === 'ORG_ADMIN' || role === 'SUPER_ADMIN') {
    items.push({ to: '/org', label: 'Dokumen Saya', icon: FileText })
    items.push({ to: '/org/upload', label: 'Upload PDF', icon: Upload })
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
