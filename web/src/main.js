import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { setNotify } from './api'
import { useShopStore } from './stores'
import './styles/base.css'
import './styles/common.css'
import './styles/home.css'
import './styles/pages.css'
import './styles/search.css'
import './styles/item.css'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia).use(router)

const shop = useShopStore(pinia)
setNotify((msg) => shop.showToast(msg))
shop.refreshMe()

app.mount('#app')
