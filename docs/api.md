# 接口清单

统一前缀 `/api/v1/`，统一响应 `{code, msg, data}`（`code=0` 成功），分页响应 `{page, size, total, results}`。
认证方式为 JWT：请求头 `Authorization: Bearer <access>`。

## 1. 认证

| 方法 | 路径 | 认证 | 说明 |
| --- | --- | --- | --- |
| POST | `/auth/login/` | 否 | 手机号 + 密码登录，返回 `access` / `refresh` / `user` |
| POST | `/auth/register/` | 否 | 注册买家，`captcha` 固定 `8888` |
| POST | `/auth/refresh/` | 否 | 用 refresh 换 access |
| GET/PATCH | `/auth/me/` | 是 | 当前用户信息 / 修改昵称、邮箱 |
| GET | `/auth/summary/` | 是 | 个人中心角标：各状态订单数、地址数、券数 |

## 2. 商城内容与商品

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/home/` | 首页聚合：类目树、轮播、快报、楼层（含商品）、秒杀、猜你喜欢、优惠券 |
| GET | `/categories/` | 三级类目树（仅启用项） |
| GET | `/brands/` | 品牌列表，可传 `category` 过滤 |
| GET | `/banners/` | 轮播图（启用） |
| GET | `/notices/` | 快报（启用） |
| GET | `/floors/` | 首页楼层（启用） |
| GET | `/products/` | 商品列表 / 搜索 / 筛选 / 排序 / 分页 |
| GET | `/products/{id}/` | 商品详情：SKU、评价、店铺、类目路径、相关推荐 |
| GET | `/products/{id}/reviews/` | 商品评价分页，可传 `rating` |
| GET | `/seckill/` | 秒杀场次与商品 |
| GET | `/coupons/` | 优惠券列表，`mine=1` 查已领（需登录） |
| POST | `/coupons/` | 领取优惠券（需登录） |

`/products/` 查询参数：

| 参数 | 说明 |
| --- | --- |
| `q` | 关键词，匹配标题 / 副标题 / 标签 / 品牌名 / 三级类目及其上级类目名 |
| `category` | 类目 ID（自动包含所有后代类目） |
| `brand` | 品牌 ID，多选用逗号分隔 |
| `shop` | 店铺 ID |
| `min_price` / `max_price` | 价格区间（按最低 SKU 价） |
| `in_stock=1` | 仅看有货 |
| `ordering` | `default` / `sales` / `new` / `price_asc` / `price_desc` / `rating` |
| `floor` + `tab` | 楼层 Tab 取数（热门 / 新品 / 价格） |
| `page` / `size` | 分页，`size` 最大 60 |

## 3. 购物车

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/cart/` | 购物车列表（含店铺、库存、是否有效） |
| POST | `/cart/` | 加入购物车 `{sku_id, quantity}` |
| DELETE | `/cart/` | 删除已勾选商品 |
| PATCH | `/cart/{id}/` | 修改数量 / 勾选状态 |
| DELETE | `/cart/{id}/` | 删除单条 |
| POST | `/cart/toggle/` | 全选 / 取消全选 `{selected}` |

## 4. 地址、订单与支付

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET/POST | `/addresses/` | 地址列表 / 新增（首条自动设默认） |
| PATCH/DELETE | `/addresses/{id}/` | 修改 / 删除 |
| GET | `/orders/` | 我的订单分页，`status` 过滤，`q` 搜商品标题 |
| POST | `/orders/` | 提交订单：购物车勾选项按店铺拆单；传 `sku_id` 走「立即购买」 |
| GET | `/orders/{order_no}/` | 订单详情（含商品、金额、物流、售后记录） |
| GET | `/orders/batch/{batch_no}/` | 批次（同一次结算的多店铺订单） |
| POST | `/orders/{order_no}/cancel/` | 取消待付款订单，事务内回滚库存 |
| POST | `/orders/{order_no}/confirm/` | 确认收货 |
| POST | `/payment/mock/` | Mock 支付，支持 `order_no` 或 `batch_no` |
| POST | `/reviews/` | 已完成订单评价（支持逐件评分与正文） |
| GET | `/reviews/mine/` | 我的评价 |
| GET/POST | `/aftersales/` | 我的售后列表 / 提交售后申请（订单转「售后中」） |

订单金额规则：单店铺小计满 99 元免运费，否则 8 元；`subtotal`、`freight`、`total` 均由后端计算。

## 5. 商家后台（数据隔离：仅本店）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/merchant/dashboard/` | 看板：店铺信息、统计、近 7 日趋势、热销 Top5、最近订单 |
| GET/POST | `/merchant/products/` | 本店商品分页 / 新增（新增默认待审核） |
| PATCH | `/merchant/products/{id}/` | 编辑标题、类目、品牌、价格、库存、状态 |
| POST | `/merchant/products/{id}/toggle/` | 上架 / 下架 |
| GET | `/merchant/orders/` | 本店订单分页，`status` / `q` 过滤 |
| POST | `/merchant/orders/{order_no}/ship/` | 发货 `{tracking_no, tracking_company}` |
| GET/POST | `/merchant/aftersales/` | 售后列表 / 处理 `{id, action, reply}`（同意回滚库存） |
| GET/PATCH | `/merchant/shop/` | 店铺资料 |

## 6. 平台后台（跨店）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/console/dashboard/` | 全站 GMV、订单、买家、店铺、待办、趋势、店铺排行、类目分布 |
| GET/POST | `/console/categories/` | 类目树（含停用项）/ 新增类目 |
| PATCH/DELETE | `/console/categories/{id}/` | 改名、启停、排序 / 删除（子类目与商品保护） |
| GET | `/console/shops/` | 店铺列表，`approved=true/false`、`q` 过滤 |
| POST | `/console/shops/{id}/audit/` | `approve` / `reject` / `disable` / `enable` |
| GET | `/console/products/` | 全站商品分页，`status` / `q` / `shop` 过滤 |
| POST | `/console/products/{id}/audit/` | `approve` / `reject`（带 reason）/ `off` / `on` |
| GET | `/console/orders/` | 跨店订单分页，`status` / `q` / `shop` 过滤 |
| GET/POST | `/console/aftersales/` | 售后工单列表 / 平台处理（同意退款会回滚库存） |
| GET/POST | `/console/banners/` | 轮播列表 / 新增 |
| PATCH/DELETE | `/console/banners/{id}/` | 编辑 / 删除 |
| GET/POST | `/console/floors/` | 楼层列表 / 新增 |
| PATCH/DELETE | `/console/floors/{id}/` | 编辑 / 删除 |
| GET/POST | `/console/notices/` | 快报列表 / 新增 |
| PATCH/DELETE | `/console/notices/{id}/` | 编辑 / 删除 |
| GET | `/console/users/` | 用户分页，`role` / `q` 过滤 |
| POST | `/console/users/{id}/toggle/` | 禁用 / 启用（平台账号不可禁用） |
| GET/POST | `/console/coupons/` | 优惠券列表 / 新建 |
| PATCH/DELETE | `/console/coupons/{id}/` | 启停 / 删除 |

## 7. 错误码

| code | 含义 |
| --- | --- |
| 0 | 成功 |
| 40001 | 参数校验失败 |
| 40101 / 40102 | 未登录 / 登录过期 |
| 40301 / 40302 | 账号禁用 / 未绑定店铺 |
| 40404 | 资源不存在 |
| 50000 | 服务器内部错误 |

HTTP 状态码与语义对齐（400 / 401 / 403 / 404 / 500），前端统一拦截后 Toast 提示。
