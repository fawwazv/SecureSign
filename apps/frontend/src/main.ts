import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { registerDashboardRoutes } from './router/dashboard.routes'
import './assets/styles/main.css'

// FE2: daftarkan rute dashboard via addRoute (tanpa mengubah router/index.ts milik FE1).
registerDashboardRoutes(router)

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
