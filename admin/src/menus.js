export const ROLE_LABEL = { merchant: '商家中心', console: '平台管理' }

export const MENUS = {
  merchant: [
    { key: 'dashboard', label: '数据看板', icon: 'grid', path: '/merchant/dashboard' },
    { key: 'products', label: '商品管理', icon: 'box', path: '/merchant/products' },
    { key: 'orders', label: '订单管理', icon: 'list', path: '/merchant/orders', badge: 'pending_ship' },
    {
      key: 'aftersales',
      label: '售后管理',
      icon: 'refresh',
      path: '/merchant/aftersales',
      badge: 'pending_aftersale',
    },
    { key: 'shop', label: '店铺设置', icon: 'shop', path: '/merchant/shop' },
  ],
  console: [
    { key: 'dashboard', label: '数据看板', icon: 'grid', path: '/console/dashboard' },
    { key: 'categories', label: '类目管理', icon: 'tree', path: '/console/categories' },
    { key: 'shops', label: '商家审核', icon: 'shop', path: '/console/shops', badge: 'pending_shops' },
    { key: 'products', label: '商品审核', icon: 'box', path: '/console/products', badge: 'pending_products' },
    { key: 'orders', label: '订单中心', icon: 'list', path: '/console/orders' },
    { key: 'content', label: '内容运营', icon: 'star', path: '/console/content' },
    { key: 'users', label: '用户管理', icon: 'user', path: '/console/users' },
  ],
}

export const ORDER_STATUS = [
  { value: 'pending_pay', label: '等待付款' },
  { value: 'paid', label: '等待发货' },
  { value: 'shipped', label: '等待收货' },
  { value: 'completed', label: '已完成' },
  { value: 'aftersale', label: '售后中' },
  { value: 'cancelled', label: '已取消' },
  { value: 'refunded', label: '已退款' },
]

export const PRODUCT_STATUS = [
  { value: 'on', label: '在售', type: 'success' },
  { value: 'pending', label: '待审核', type: 'warning' },
  { value: 'off', label: '已下架', type: 'info' },
  { value: 'rejected', label: '审核驳回', type: 'danger' },
  { value: 'draft', label: '草稿', type: 'info' },
]

export const statusLabel = (value) => ORDER_STATUS.find((s) => s.value === value)?.label || value || '-'
export const productStatus = (value) =>
  PRODUCT_STATUS.find((s) => s.value === value) || { label: value, type: 'info' }
