import { defineStore } from 'pinia'

export type NotificationKind = 'info' | 'success' | 'warning' | 'error'

export interface AppNotification {
  id: string
  kind: NotificationKind
  title: string
  message?: string
  at: string
  read: boolean
}

function uid(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`
}

export const useNotificationStore = defineStore('notification', {
  state: () => ({
    items: [] as AppNotification[],
  }),
  getters: {
    unreadCount: (s) => s.items.filter((i) => !i.read).length,
  },
  actions: {
    push(kind: NotificationKind, title: string, message?: string) {
      this.items.unshift({ id: uid(), kind, title, message, at: new Date().toISOString(), read: false })
      if (this.items.length > 50) this.items.length = 50
    },
    markAllRead() {
      this.items.forEach((i) => (i.read = true))
    },
    clear() {
      this.items = []
    },
  },
})
