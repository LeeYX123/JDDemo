# 目录结构

```text
JD_Demo/
├─ backend/                        Django 5 + DRF 后端
│  ├─ .env / .env.example          环境变量（DB_ENGINE 支持 mysql / sqlite）
│  ├─ manage.py
│  ├─ jdshop/
│  │  ├─ settings.py               数据库、JWT、CORS、DRF 统一异常处理
│  │  ├─ urls.py                   挂载 /api/v1/
│  │  └─ wsgi.py
│  └─ store/
│     ├─ models.py                 User/Address/Category/Brand/Shop/Spu/Sku/
│     │                            CartItem/Order/OrderItem/Review/AfterSale/
│     │                            Banner/Notice/HomeFloor/Seckill*/Coupon
│     ├─ serializers.py            列表/详情/购物车/订单/售后/内容序列化
│     ├─ permissions.py            IsMerchant / IsConsole
│     ├─ responses.py              ok() / fail() / exception_handler
│     ├─ utils.py                  订单号生成、统一分页、类目作用域
│     ├─ admin.py                  Django Admin 调试入口
│     ├─ migrations/
│     ├─ management/commands/
│     │  ├─ seed_demo.py           一键造数（幂等）
│     │  └─ reset_demo.py          flush + 重建演示数据
│     └─ views/
│        ├─ auth.py                登录/注册/刷新/me/summary
│        ├─ catalog.py             首页聚合、类目、商品、搜索、秒杀、优惠券
│        ├─ cart.py                购物车增删改查与全选
│        ├─ orders.py              地址、下单、支付、订单动作、评价、售后
│        ├─ merchant.py            商家看板/商品/订单/售后/店铺
│        └─ console.py             平台看板/类目/商家/商品审核/订单/内容/用户
│
├─ web/                            买家端 Vue 3 SPA（5173）
│  ├─ index.html
│  ├─ vite.config.js               /api 代理、vendor 分包、SPA history
│  └─ src/
│     ├─ main.js / App.vue / router.js / stores.js / api.js
│     ├─ components/               TopBar/SiteHeader/SiteNav/CategoryMenu/
│     │                            HeroCarousel/QuickPanel/PromoColumn/
│     │                            SeckillFloor/ProductFloor/ProductCard/
│     │                            ProductImage/Icon/Logo/SiteFooter/ShopLayout
│     ├─ pages/                    Home/Search/Item/Cart/Checkout/Pay/Orders/
│     │                            OrderDetail/User/Coupons/Seckill/Auth/NotFound
│     └─ styles/                   base/common/home/pages/search/item
│
├─ admin/                          运营后台 Vue 3 + Element Plus SPA（5174）
│  ├─ index.html
│  ├─ vite.config.js               /api 代理、vendor 与 element 分包
│  └─ src/
│     ├─ main.js / App.vue / router.js（角色路由守卫）/ api.js
│     ├─ menus.js                  双角色菜单与状态字典
│     ├─ store/auth.js             登录态与角色
│     ├─ layouts/AdminLayout.vue   侧栏 + 顶栏 + 角色配色切换
│     ├─ components/               PageHead/StatCard/TrendChart/AppIcon
│     ├─ views/Login.vue
│     ├─ views/merchant/           Dashboard/Products/Orders/Aftersales/Shop
│     ├─ views/console/            Dashboard/Categories/Shops/Products/
│     │                            Orders/Content/Users
│     └─ styles/                   base/components/views
│
├─ scripts/
│  ├─ start.bat / start.sh         一键启动（缺环境自动下载、依赖自动修复）
│  ├─ start-debug.bat              排查用：结束后保留窗口
│  ├─ stop.bat / stop.sh           按端口停止三个服务
│  ├─ serve_django.bat             内部启动器（独立窗口 + 写日志）
│  ├─ serve_web.bat / serve_admin.bat
│  ├─ bootstrap.ps1                Windows 运行环境自举：探测/下载/安装 Python、Node
│  ├─ tools/prepare.py             虚拟环境与依赖准备：健康检查、按哈希增量安装
│  ├─ init_db.py                   按 .env 创建 MySQL 库（sqlite 跳过）
│  ├─ smoke.py                     端到端冒烟（仅标准库）
│  └─ logs/                        运行日志（启动后生成，含 env.cmd）
│
├─ docs/
│  ├─ pages.md                     页面清单与交互要点
│  ├─ api.md                       接口清单
│  ├─ er.md                        ER 图
│  ├─ order-state.md               订单状态机
│  ├─ structure.md                 本文件
│  ├─ visual-spec.md               视觉规范表
│  ├─ acceptance.md                验收自检记录
│  └─ screenshots/                 实跑截图（首页 / 详情 / 双端看板 / 支付成功）
│
├─ package.json                    根级 lint / format / build / smoke 脚本
├─ .runtime/                       自动下载的便携 Python / Node（gitignore，可删）
├─ eslint.config.js                前端 ESLint（flat config + prettier 兼容）
├─ .prettierrc.json
├─ pyproject.toml                  ruff + black 配置
├─ requirements.txt
├─ README.md
└─ prompt.md                       需求说明
```
