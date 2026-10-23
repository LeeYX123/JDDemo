import { defineStore } from 'pinia'

import { api } from './api'

/**
 * 买家端全局状态：登录用户、购物车、全局 Toast。
 * 所有接口返回都已在 request 层解包为 {code:0,data} 里的 data，
 * 因此这里直接拿到业务数据，不再判断 code。
 */
export const useShopStore = defineStore('shop', {
  state: () => ({
    cart: [],
    user: JSON.parse(localStorage.getItem('jd_user') || 'null'),
    toast: '',
    cartLoading: false,
    toastTimer: null,
  }),

  getters: {
    isLogin: (state) => Boolean(localStorage.getItem('jd_access') && state.user),
    validCart: (state) => state.cart.filter((item) => item.valid),
    invalidCart: (state) => state.cart.filter((item) => !item.valid),
    cartCount: (state) =>
      state.cart.filter((item) => item.valid).reduce((sum, item) => sum + item.quantity, 0),
    selectedCart: (state) => state.cart.filter((item) => item.valid && item.selected),
    selectedCount: (state) => state.cart.filter((item) => item.valid && item.selected).length,
    cartTotal: (state) =>
      state.cart
        .filter((item) => item.valid && item.selected)
        .reduce((sum, item) => sum + Number(item.price) * item.quantity, 0),
  },

  actions: {
    /* ------------------------------------------------------------ 提示 */
    showToast(text) {
      this.toast = text
      if (this.toastTimer) clearTimeout(this.toastTimer)
      this.toastTimer = setTimeout(() => {
        this.toast = ''
        this.toastTimer = null
      }, 2200)
    },

    /* ------------------------------------------------------------ 登录态 */
    setUser(user, access) {
      this.user = user || null
      if (user) {
        localStorage.setItem('jd_user', JSON.stringify(user))
        if (access) localStorage.setItem('jd_access', access)
      } else {
        localStorage.removeItem('jd_user')
      }
    },

    async refreshMe() {
      if (!localStorage.getItem('jd_access')) return null
      try {
        const me = await api.get('/auth/me/')
        this.setUser(me)
        await this.loadCart()
        return me
      } catch {
        return null
      }
    },

    async login(username, password) {
      const data = await api.post('/auth/login/', { username, password })
      localStorage.setItem('jd_access', data.access)
      if (data.refresh) localStorage.setItem('jd_refresh', data.refresh)
      this.setUser(data.user)
      await this.loadCart()
      return data.user
    },

    logout() {
      this.user = null
      this.cart = []
      localStorage.removeItem('jd_user')
      localStorage.removeItem('jd_access')
      localStorage.removeItem('jd_refresh')
      this.showToast('已退出登录')
    },

    /* ------------------------------------------------------------ 购物车 */
    async loadCart() {
      if (!localStorage.getItem('jd_access')) {
        this.cart = []
        return []
      }
      this.cartLoading = true
      try {
        this.cart = (await api.get('/cart/')) || []
        return this.cart
      } finally {
        this.cartLoading = false
      }
    },

    async addCart(skuId, quantity = 1) {
      const rows = await api.post('/cart/', { sku_id: skuId, quantity })
      if (Array.isArray(rows)) this.cart = rows
      else await this.loadCart()
      this.showToast('已加入购物车')
      return this.cart
    },

    async updateCart(id, patch) {
      const rows = await api.patch(`/cart/${id}/`, patch)
      if (Array.isArray(rows)) this.cart = rows
    },

    async removeCart(id) {
      const rows = await api.delete(`/cart/${id}/`)
      if (Array.isArray(rows)) this.cart = rows
      this.showToast('已删除该商品')
    },

    async removeSelected() {
      if (!this.selectedCount) {
        this.showToast('请先选择商品')
        return
      }
      const rows = await api.delete('/cart/')
      if (Array.isArray(rows)) this.cart = rows
      this.showToast('已删除选中商品')
    },

    async toggleAll(selected) {
      const rows = await api.post('/cart/toggle/', { selected })
      if (Array.isArray(rows)) this.cart = rows
    },
  },
})
