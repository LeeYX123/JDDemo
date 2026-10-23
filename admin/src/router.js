import { createRouter, createWebHistory } from 'vue-router'

import AdminLayout from './layouts/AdminLayout.vue'
import { useAuthStore } from './store/auth'

const routes = [
  { path: '/login', name: 'login', component: () => import('./views/Login.vue'), meta: { public: true } },
  {
    path: '/merchant',
    component: AdminLayout,
    meta: { role: 'merchant', allowConsole: true },
    children: [
      { path: '', redirect: '/merchant/dashboard' },
      {
        path: 'dashboard',
        name: 'm-dashboard',
        component: () => import('./views/merchant/Dashboard.vue'),
        meta: { title: '数据看板' },
      },
      {
        path: 'products',
        name: 'm-products',
        component: () => import('./views/merchant/Products.vue'),
        meta: { title: '商品管理' },
      },
      {
        path: 'orders',
        name: 'm-orders',
        component: () => import('./views/merchant/Orders.vue'),
        meta: { title: '订单管理' },
      },
      {
        path: 'aftersales',
        name: 'm-aftersales',
        component: () => import('./views/merchant/Aftersales.vue'),
        meta: { title: '售后管理' },
      },
      {
        path: 'shop',
        name: 'm-shop',
        component: () => import('./views/merchant/Shop.vue'),
        meta: { title: '店铺设置' },
      },
    ],
  },
  {
    path: '/console',
    component: AdminLayout,
    meta: { role: 'console' },
    children: [
      { path: '', redirect: '/console/dashboard' },
      {
        path: 'dashboard',
        name: 'c-dashboard',
        component: () => import('./views/console/Dashboard.vue'),
        meta: { title: '数据看板' },
      },
      {
        path: 'categories',
        name: 'c-categories',
        component: () => import('./views/console/Categories.vue'),
        meta: { title: '类目管理' },
      },
      {
        path: 'shops',
        name: 'c-shops',
        component: () => import('./views/console/Shops.vue'),
        meta: { title: '商家审核' },
      },
      {
        path: 'products',
        name: 'c-products',
        component: () => import('./views/console/Products.vue'),
        meta: { title: '商品审核' },
      },
      {
        path: 'orders',
        name: 'c-orders',
        component: () => import('./views/console/Orders.vue'),
        meta: { title: '订单中心' },
      },
      {
        path: 'content',
        name: 'c-content',
        component: () => import('./views/console/Content.vue'),
        meta: { title: '内容运营' },
      },
      {
        path: 'users',
        name: 'c-users',
        component: () => import('./views/console/Users.vue'),
        meta: { title: '用户管理' },
      },
    ],
  },
  {
    path: '/',
    redirect: () => {
      const auth = useAuthStore()
      return auth.role === 'console' ? '/console/dashboard' : '/merchant/dashboard'
    },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: () => {
      const auth = useAuthStore()
      return auth.role === 'console' ? '/console/dashboard' : '/merchant/dashboard'
    },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach((to) => {
  const auth = useAuthStore()

  if (to.meta.public) {
    if (auth.isLogin) return auth.homePath
    return true
  }

  const requiredRole = to.matched.find((record) => record.meta.role)?.meta.role
  if (!requiredRole) return true

  if (!auth.isLogin) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  const allowConsole = to.matched.some((record) => record.meta.allowConsole)
  const roleOk = auth.role === requiredRole || (allowConsole && auth.role === 'console')
  if (!roleOk) return auth.homePath

  return true
})

export default router
