import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'

import App from './App.vue'
import router from './router'
import './styles/base.css'
import './styles/components.css'
import './styles/views.css'

const app = createApp(App)
app.use(createPinia()).use(ElementPlus, { locale: zhCn }).use(router)
app.mount('#app')
