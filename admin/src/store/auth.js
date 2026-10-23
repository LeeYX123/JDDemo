import { defineStore } from 'pinia'

import { api } from '../api'

const readUser = () => {
  try {
    return JSON.parse(localStorage.getItem('jd_admin_user') || 'null')
  } catch {
    return null
  }
}

/** 后台登录态：一个 SPA 承载商家与平台两种角色。 */
export const useAuthStore = defineStore('adminAuth', {
  state: () => ({
    token: localStorage.getItem('jd_admin_access') || '',
    user: readUser(),
  }),

  getters: {
    isLogin: (state) => Boolean(state.token && state.user),
    role: (state) => state.user?.role || '',
    isMerchant: (state) => state.user?.role === 'merchant',
    isConsole: (state) => state.user?.role === 'console',
    homePath: (state) => (state.user?.role === 'console' ? '/console/dashboard' : '/merchant/dashboard'),
    displayName: (state) => state.user?.nickname || state.user?.username || '未登录',
  },

  actions: {
    async login(username, password) {
      const data = await api.post('/auth/login/', { username, password })
      if (!['merchant', 'console'].includes(data.user.role)) {
        const error = new Error('该账号不是商家或平台账号，请使用买家端登录')
        error.code = 'ROLE'
        throw error
      }
      this.token = data.access
      this.user = data.user
      localStorage.setItem('jd_admin_access', data.access)
      localStorage.setItem('jd_admin_user', JSON.stringify(data.user))
      return data.user
    },

    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('jd_admin_access')
      localStorage.removeItem('jd_admin_user')
    },
  },
})
