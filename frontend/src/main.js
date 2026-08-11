import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import './assets/main.css'
import './lib/chart'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
