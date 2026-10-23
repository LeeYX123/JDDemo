import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'home', component: () => import('./pages/Home.vue') },
  { path: '/search', name: 'search', component: () => import('./pages/Search.vue') },
  { path: '/item/:id', name: 'item', component: () => import('./pages/Item.vue') },
  { path: '/cart', name: 'cart', component: () => import('./pages/Cart.vue'), meta: { auth: true } },
  {
    path: '/checkout',
    name: 'checkout',
    component: () => import('./pages/Checkout.vue'),
    meta: { auth: true },
  },
  { path: '/pay/:orderNo', name: 'pay', component: () => import('./pages/Pay.vue'), meta: { auth: true } },
  { path: '/orders', name: 'orders', component: () => import('./pages/Orders.vue'), meta: { auth: true } },
  {
    path: '/orders/:orderNo',
    name: 'order-detail',
    component: () => import('./pages/OrderDetail.vue'),
    meta: { auth: true },
  },
  { path: '/user', name: 'user', component: () => import('./pages/User.vue'), meta: { auth: true } },
  { path: '/coupons', name: 'coupons', component: () => import('./pages/Coupons.vue') },
  { path: '/seckill', name: 'seckill', component: () => import('./pages/Seckill.vue') },
  { path: '/login', name: 'login', component: () => import('./pages/Auth.vue') },
  { path: '/register', name: 'register', component: () => import('./pages/Auth.vue') },
  { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('./pages/NotFound.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    return { top: 0 }
  },
})

router.beforeEach((to) => {
  if (to.meta.auth && !localStorage.getItem('jd_access')) {
    return { path: '/login', query: { next: to.fullPath } }
  }
  if (to.name === 'login' && localStorage.getItem('jd_access')) {
    return { path: '/' }
  }
  return true
})

export default router
